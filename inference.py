import os
import json
import asyncio
import argparse
from typing import List, Optional
from openai import OpenAI
from client import SupportTicketTriageEnv
from models import SupportTicketTriageAction

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
API_KEY = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """You are a high-performance support triage agent. 

MANDATORY WORKFLOW:
1. SEARCH: If the ticket is technical or has specific error codes, use {"action_type": "search_kb", "search_query": "..."} to find the resolution.
2. TRIAGE: You MUST use {"action_type": "update_ticket", "team": "...", "priority": "...", "status": "..."} to route the ticket correctly.
   - Teams: billing, it_support, product, hardware.
   - Priorities: low, medium, high, critical.
   - Statuses: in_progress, resolved.
3. REPLY: Use {"action_type": "reply", "reply_text": "..."} to provide the solution found in the KB to the customer.
4. SUBMIT: Once triage is done and the reply is drafted, you MUST use {"action_type": "submit"} to finalize.

YOU MUST CALL "submit" TO FINISH THE TASK. DO NOT REPEAT THE SAME ACTION.
Output ONLY a valid JSON object. No markdown."""

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

async def run_task(client: OpenAI, env_url: str, task_level: str):
    env = SupportTicketTriageEnv(env_url)
    log_start(task=task_level, env="support_ticket_triage", model=MODEL_NAME)
    
    rewards = []
    steps_taken = 0
    success = False
    
    try:
        # 1. Reset and Start
        obs = await env.reset()
        res = await env.step(SupportTicketTriageAction(action_type="start_task", task_level=task_level))
        obs = res.observation
        
        history = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        for step_idx in range(1, 11):
            steps_taken = step_idx
            
            # Get action from LLM
            prompt = f"Ticket: {obs.current_ticket}\nKB: {obs.kb_search_results}\nStatus: {obs.ticket_status}\nPriority: {obs.ticket_priority}\nTeam: {obs.ticket_team}\nMsg: {obs.system_message}"
            history.append({"role": "user", "content": prompt})
            
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=history,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            action_str = completion.choices[0].message.content
            
            try:
                action_json = json.loads(action_str)
                action_obj = SupportTicketTriageAction(**action_json)
            except Exception as e:
                action_obj = SupportTicketTriageAction(action_type="submit")

            # --- Loop Prevention Logic ---
            is_redundant = False
            if action_obj.action_type == "reply":
                current_reply = action_obj.reply_text
                # Check if we've sent this exact reply in the last 2 steps
                recent_replies = [h.get("content", "") for h in history if isinstance(h, dict) and current_reply in str(h.get("content", ""))]
                if len(recent_replies) >= 2:
                    is_redundant = True
            
            if is_redundant:
                # Nudge the agent to finish
                nudge = "SYSTEM: You are repeating yourself. If you have provided the answer, you MUST call 'update_ticket' with the correct team/priority and then 'submit'."
                history.append({"role": "user", "content": nudge})
                # Re-run LLM with the nudge
                try:
                    completion = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=history,
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    action_str = completion.choices[0].message.content
                    action_json = json.loads(action_str)
                    action_obj = SupportTicketTriageAction(**action_json)
                except:
                    action_obj = SupportTicketTriageAction(action_type="submit")

            # Step the environment
            res = await env.step(action_obj)
            obs = res.observation
            rewards.append(res.reward)
            
            log_step(step=step_idx, action=action_obj.model_dump_json(), reward=res.reward, done=res.done, error=None)
            
            if res.done:
                break
                
        final_score = sum(rewards)
        success = final_score > 0.5 # Threshold for success

    except Exception as e:
        print(f"Error during inference: {e}")
        final_score = 0.0
    
    log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:7860")
    args = parser.parse_args()

    if not API_KEY or API_KEY == "your-groq-api-key":
        print("CRITICAL: OPENAI_API_KEY is not set correctly. Please export your real Groq key.")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    for level in ["easy", "medium", "hard"]:
        print(f"\n--- Processing {level.upper()} ---")
        await run_task(client, args.url, level)

if __name__ == "__main__":
    asyncio.run(main())
