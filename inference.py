"""
Inference Script — Support Ticket Triage OpenEnv
===================================
MANDATORY variables (read from environment):
    API_BASE_URL   The API endpoint for the LLM.
                   Default: "https://router.huggingface.co/v1"
    MODEL_NAME     The model identifier to use for inference.
                   Default: "Qwen/Qwen2.5-72B-Instruct"
    HF_TOKEN       Your Hugging Face / API key.  NO default — must be set.

Usage:
    export HF_TOKEN="hf_..."
    export API_BASE_URL="https://router.huggingface.co/v1"   # optional
    export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"            # optional
    python inference.py --url http://localhost:7860

STDOUT FORMAT (strictly followed):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.00> rewards=<r1,r2,...,rn>
"""

import os
import re
import json
import asyncio
import argparse
from typing import List, Optional

from openai import OpenAI

from client import SupportTicketTriageEnv
from models import SupportTicketTriageAction

# ---------------------------------------------------------------------------
# Configuration — defaults set ONLY for API_BASE_URL and MODEL_NAME (not HF_TOKEN)
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME   = os.getenv("MODEL_NAME")   or "Qwen/Qwen2.5-72B-Instruct"
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

# Optional — only needed if launching env from a local Docker image
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

BENCHMARK    = "support_ticket_triage"
MAX_STEPS    = 10
SUCCESS_THRESHOLD = 0.5

SYSTEM_PROMPT = """You are an elite support triage agent.

MANDATORY OUTPUT FORMAT:
Output ONLY a valid JSON object with exactly two keys:
1. "thinking": Your step-by-step reasoning as a string.
2. "action":   The action object.

ALLOWED VALUES (STRICT — any deviation will fail validation):
  action_type : "search_kb" | "update_ticket" | "reply" | "submit"
  team        : "billing" | "it_support" | "product" | "hardware" | "security" | "hr"
  priority    : "low" | "medium" | "high" | "critical" | "urgent"
  status      : "open" | "in_progress" | "resolved" | "escalated"

OPTIMAL WORKFLOW (complete within 6 steps to minimise penalties):
  1. search_kb  — query the KB with specific keywords from the ticket.
  2. update_ticket — set team, priority, and status in ONE call.
  3. reply      — draft a concise but complete resolution using KB facts.
  4. submit     — finalise and receive your score.

Output ONLY JSON. No markdown fences. No extra keys."""


# ---------------------------------------------------------------------------
# Structured stdout loggers — exact format required by the hackathon spec
# ---------------------------------------------------------------------------
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val  = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_final_score(system_message: str) -> Optional[float]:
    """Parse the authoritative score that the environment embeds in its submit message.

    Environment emits: "Task submitted. Final score: 0.93/1.00"
    """
    match = re.search(r"Final score:\s*([\d.]+)", system_message or "")
    return float(match.group(1)) if match else None


def _build_prompt(obs) -> str:
    return (
        f"Ticket: {obs.current_ticket}\n"
        f"KB Results: {obs.kb_search_results or '(none yet)'}\n"
        f"Status: {obs.ticket_status}  |  Priority: {obs.ticket_priority}  |  Team: {obs.ticket_team}\n"
        f"Draft reply: {obs.draft_reply or '(none yet)'}\n"
        f"System msg: {obs.system_message}"
    )


def _safe_action(response_json: dict) -> SupportTicketTriageAction:
    """Extract and sanitise the action from the LLM JSON response."""
    action_data = response_json.get("action", response_json)

    # Normalise any alternate reply key names
    for alias in ("message", "response", "msg", "draft", "text"):
        if alias in action_data and "reply_text" not in action_data:
            action_data["reply_text"] = action_data.pop(alias)

    # Only pass keys the model accepts (extra='ignore' in Pydantic handles the rest)
    allowed = {"action_type", "task_level", "search_query", "priority", "team", "status", "reply_text"}
    sanitised = {k: v for k, v in action_data.items() if k in allowed and v is not None}

    if "action_type" not in sanitised:
        sanitised["action_type"] = "search_kb"
    if sanitised["action_type"] == "search_kb" and not sanitised.get("search_query"):
        sanitised["search_query"] = "support issue"

    return SupportTicketTriageAction(**sanitised)


# ---------------------------------------------------------------------------
# Core episode runner
# ---------------------------------------------------------------------------
async def run_task(client: OpenAI, env_url: str, task_level: str) -> None:
    """Run one full episode for the given difficulty level and emit spec logs."""

    env = SupportTicketTriageEnv(env_url)

    rewards:     List[float] = []
    steps_taken: int         = 0
    final_score: float       = 0.01
    success:     bool        = False

    log_start(task=task_level, env=BENCHMARK, model=MODEL_NAME)

    try:
        # ---- Episode initialisation ----------------------------------------
        await env.reset()
        res = await env.step(SupportTicketTriageAction(action_type="start_task", task_level=task_level))
        obs = res.observation

        history: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # ---- Agent loop ----------------------------------------------------
        for step_idx in range(1, MAX_STEPS + 1):
            steps_taken = step_idx

            # Build user prompt
            prompt = _build_prompt(obs)
            history.append({"role": "user", "content": prompt})

            # LLM call — always via the OpenAI-compatible client
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=history,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                raw = completion.choices[0].message.content or "{}"
                response_json = json.loads(raw)
                thinking = response_json.get("thinking", "")
                print(f"[THINKING] {thinking}", flush=True)
                action_obj = _safe_action(response_json)
                history.append({"role": "assistant", "content": raw})

            except Exception as parse_err:
                print(f"[DEBUG] LLM/parse error at step {step_idx}: {parse_err}", flush=True)
                action_obj = SupportTicketTriageAction(action_type="search_kb", search_query="support issue")
                history.append({"role": "assistant", "content": json.dumps({
                    "thinking": f"Error — falling back to search: {parse_err}",
                    "action": action_obj.model_dump()
                })})

            # ---- Loop-prevention nudge ------------------------------------
            if action_obj.action_type == "reply" and action_obj.reply_text:
                prior_replies = sum(
                    1 for h in history
                    if h.get("role") == "assistant"
                    and action_obj.reply_text in str(h.get("content", ""))
                )
                if prior_replies >= 2:
                    nudge = (
                        "SYSTEM: You are repeating yourself. "
                        "Your reply draft is already saved. "
                        "You MUST now call 'update_ticket' to set team/priority/status, then 'submit'."
                    )
                    history.append({"role": "user", "content": nudge})
                    try:
                        c2 = client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=history,
                            temperature=0.1,
                            response_format={"type": "json_object"},
                        )
                        r2 = json.loads(c2.choices[0].message.content or "{}")
                        action_obj = _safe_action(r2)
                        history.append({"role": "assistant", "content": c2.choices[0].message.content})
                    except Exception:
                        action_obj = SupportTicketTriageAction(action_type="submit")

            # ---- Environment step -----------------------------------------
            res = await env.step(action_obj)
            obs = res.observation
            rewards.append(res.reward)

            log_step(
                step=step_idx,
                action=action_obj.model_dump_json(),
                reward=res.reward,
                done=res.done,
                error=None,
            )

            if res.done:
                # The environment embeds the authoritative score in system_message
                extracted = _extract_final_score(obs.system_message)
                if extracted is not None:
                    final_score = extracted
                break

        # Fallback: if submit wasn't reached, clamp accumulated reward
        if final_score <= 0.01 and rewards:
            # Potential-based rewards sum ≈ Φ(final) − Φ(initial); clamp to [0.01, 0.99]
            final_score = min(max(sum(rewards), 0.01), 0.99)

        success = final_score >= SUCCESS_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Episode error for {task_level}: {exc}", flush=True)
        final_score = 0.01
        success = False

    finally:
        # Guaranteed log_end — always fires even on exception
        log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline agent against Support Ticket Triage env.")
    parser.add_argument("--url", default="http://localhost:7860", help="Environment server URL")
    args = parser.parse_args()

    if not API_KEY:
        print(
            "CRITICAL: No API key found. "
            "Set the HF_TOKEN (or API_KEY) environment variable before running.",
            flush=True,
        )
        return

    # Single shared OpenAI-compatible client, configured via env vars
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    for level in ["easy", "medium", "hard"]:
        print(f"\n{'='*50}", flush=True)
        print(f"  Task level: {level.upper()}", flush=True)
        print(f"{'='*50}", flush=True)
        await run_task(client, args.url, level)


if __name__ == "__main__":
    asyncio.run(main())
