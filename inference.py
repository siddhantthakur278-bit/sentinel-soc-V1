"""
SentinelAI Inference Script — Autonomous SOC Analyst
===================================================
A high-performance security agent designed for the Meta PyTorch Hackathon.
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
# Configuration
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME   = os.getenv("MODEL_NAME")   or "Qwen/Qwen2.5-72B-Instruct"
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

BENCHMARK    = "sentinel_soc"
MAX_STEPS    = 10
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
# Structured loggers
# ---------------------------------------------------------------------------
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    ev = error if error else "null"
    dv = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.3f} done={dv} error={ev}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rs = ",".join(f"{r:.3f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rs}", flush=True)

def _extract_final_score(msg: str) -> Optional[float]:
    match = re.search(r"Final score:\s*([\d.]+)", msg or "")
    return float(match.group(1)) if match else None

def _safe_action(rj: dict) -> SentinelAction:
    d = rj.get("action", rj)
    # Mapping legacy keys to new SOC format for backward/forward compatibility
    at = str(d.get("action_type", "investigate")).lower()
    if "search" in at or "invest" in at: at = "investigate"
    elif "updat" in at or "mitig" in at: at = "mitigate"
    elif "repl" in at or "repor" in at: at = "report"
    
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
    env = SentinelEnv(url)
    rewards, steps, f_score, success = [], 0, 0.01, False

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
                    model=MODEL_NAME, messages=history, temperature=0.0, response_format={"type": "json_object"}
                )
                raw = comp.choices[0].message.content or "{}"
                rj = json.loads(raw)
                print(f"[THINKING] {rj.get('thinking', 'Analyzing vectors...')}", flush=True)
                act = _safe_action(rj)
                history.append({"role": "assistant", "content": raw})
            except Exception:
                act = SentinelAction(action_type="investigate", search_query="logs")

            res = await env.step(act)
            obs = res.observation
            rewards.append(res.reward)
            log_step(i, act.model_dump_json(), res.reward, res.done, None)

            if res.done:
                f_score = _extract_final_score(obs.system_message) or 0.01
                break

        if f_score <= 0.01 and rewards:
            f_score = min(max(sum(rewards), 0.01), 0.99)
        success = f_score >= SUCCESS_THRESHOLD

    except Exception as e:
        print(f"[ERROR] Mission Critical Failure: {e}", flush=True)
        f_score = 0.01

    log_end(success, steps, f_score, rewards)

async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:7860")
    args = p.parse_args()
    if not API_KEY: return print("API_KEY missing.")
    
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    for lvl in ["easy", "medium", "hard"]:
        print(f"\n--- INITIATING MISSION: {lvl.upper()} ---")
        await run_mission(client, args.url, lvl)

if __name__ == "__main__":
    asyncio.run(main())
