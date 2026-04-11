"""
SentinelAI Inference Script — Autonomous SOC Analyst
===================================================
Meta PyTorch Hackathon — Round 1 Compliant Output
"""

import os
import re
import json
import asyncio
import argparse
from typing import List, Optional
from openai import OpenAI

# SentinelSOC Client
from client import SentinelEnv
from models import SentinelAction

# ---------------------------------------------------------------------------
# Configuration (WITH DEFAULTS AS REQUIRED BY SPEC)
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

# Validate HF_TOKEN is set (MANDATORY per spec)
if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

BENCHMARK = "sentinel_soc"
MAX_STEPS = 10
SUCCESS_THRESHOLD = 0.5

SYSTEM_PROMPT = """You are SentinelAI, an elite Autonomous SOC Analyst.
Your mission is to TRIAGE and MITIGATE incoming security incidents (alerts).

MANDATORY OUTPUT FORMAT:
Output ONLY a valid JSON object with:
1. "thinking": Your tactical reasoning (Chain of Thought).
2. "action":   The command object.

ALLOWED COMMANDS (Sentinel-DS-v3):
  action_type : "investigate" | "mitigate" | "report" | "submit"
  team        : "security" | "it_support" | "billing" | "product" | "hardware" | "hr"
  priority    : "low" | "medium" | "high" | "critical" | "urgent"
  status      : "open" | "in_progress" | "resolved" | "escalated"

TACTICAL WORKFLOW:
  1. investigate — Query the Threat Intel/Logs to identify the attack pattern.
  2. mitigate    — Reset credentials, block IPs, or isolate nodes by setting unit/severity in ONE call.
  3. report       — Draft the final incident summary for the CISO.
  4. submit      — Close the ticket and complete the mission.

Output ONLY JSON. No markdown fences."""

# ---------------------------------------------------------------------------
# Structured loggers (SPEC COMPLIANT)
# ---------------------------------------------------------------------------
def log_start(task: str, env: str, model: str) -> None:
    """[START] task=<task_name> env=<benchmark> model=<model_name>"""
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """[STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>"""
    error_val = "null" if error is None else error
    done_val = "true" if done else "false"
    # reward formatted to exactly 2 decimal places
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    """[END] success=<true|false> steps=<n> rewards=<r1,r2,...,rn>"""
    success_val = "true" if success else "false"
    # rewards formatted to 2 decimal places, comma-separated
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={success_val} steps={steps} rewards={rewards_str}", flush=True)

def _extract_final_score(msg: str) -> Optional[float]:
    match = re.search(r"Final score:\s*([\d.]+)", msg or "")
    return float(match.group(1)) if match else None

def _safe_action(rj: dict) -> SentinelAction:
    d = rj.get("action", rj)
    at = str(d.get("action_type", "investigate")).lower()
    if "search" in at or "invest" in at:
        at = "investigate"
    elif "updat" in at or "mitig" in at:
        at = "mitigate"
    elif "repl" in at or "repor" in at:
        at = "report"
    
    sanitized = {
        "action_type": at,
        "search_query": d.get("search_query", d.get("query", "threatintel")),
        "reply_text": d.get("reply_text", d.get("message", "")),
        "priority": d.get("priority"),
        "team": d.get("team"),
        "status": d.get("status")
    }
    return SentinelAction(**sanitized)

# ---------------------------------------------------------------------------
# Mission Runner
# ---------------------------------------------------------------------------
async def run_mission(client: OpenAI, url: str, level: str) -> None:
    """Run a single mission with compliant logging"""
    env = SentinelEnv(url)
    rewards = []
    steps = 0
    f_score = 0.01
    success = False
    last_action_error = None

    log_start(task=level, env=BENCHMARK, model=MODEL_NAME)

    try:
        await env.reset()
        res = await env.step(SentinelAction(action_type="start_mission", task_level=level))
        obs = res.observation
        history = [{"role": "system", "content": SYSTEM_PROMPT}]

        for i in range(1, MAX_STEPS + 1):
            steps = i
            prompt = (
                f"INCIDENT: {obs.current_ticket}\n"
                f"INTEL: {obs.kb_search_results or '(none)'}\n"
                f"STATUS: {obs.ticket_status} | SEVERITY: {obs.ticket_priority} | UNIT: {obs.ticket_team}\n"
                f"REPORT: {obs.draft_reply or '(none)'}"
            )
            history.append({"role": "user", "content": prompt})

            try:
                comp = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=history,
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                raw = comp.choices[0].message.content or "{}"
                rj = json.loads(raw)
                thinking = rj.get('thinking', 'Analyzing vectors...').replace('\n', ' ').replace('\r', '')
                print(f"[THINKING] {thinking}", file=__import__('sys').stderr, flush=True)
                act = _safe_action(rj)
                history.append({"role": "assistant", "content": raw})
            except Exception as e:
                # print(f"[THINKING] LLM error: {e}", flush=True)
                act = SentinelAction(action_type="investigate", search_query="logs")

            res = await env.step(act)
            obs = res.observation
            rewards.append(res.reward)
            
            # Capture error from environment if available
            last_action_error = getattr(res, "last_action_error", None)
            
            log_step(i, act.model_dump_json(), res.reward, res.done, last_action_error)

            if res.done:
                f_score = _extract_final_score(obs.system_message) or (sum(rewards)/len(rewards) if rewards else 0.01)
                break

        success = f_score >= SUCCESS_THRESHOLD

    except Exception as e:
        print(f"[ERROR] Mission Critical Failure: {e}", file=__import__('sys').stderr, flush=True)
        last_action_error = str(e)

    finally:
        # Hackathon spec: Emit [END] after env.close()
        try:
            await env.close()
        except Exception:
            pass
        log_end(success, steps, rewards)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:7860")
    args = parser.parse_args()
    
    # Initialize OpenAI client with specs
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    
    for lvl in ["easy", "medium", "hard"]:
        print(f"\n--- INITIATING MISSION: {lvl.upper()} ---", file=__import__('sys').stderr)
        await run_mission(client, args.url, lvl)

if __name__ == "__main__":
    asyncio.run(main())
