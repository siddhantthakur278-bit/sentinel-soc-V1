import os
import time
import json
try:
    from openai import OpenAI
except ImportError:
    print("Please install openai: pip install openai")
    exit(1)

from client import SentinelEnv
from models import SentinelAction

def run_eval(client, task_level):
    client.reset()
    start_action = SentinelAction(action_type="start_mission", task_level=task_level)
    res = client.step(start_action)
    obs = res.observation
    incident = obs.current_ticket

    system_prompt = (
        "You are SentinelAI, an elite Autonomous SOC Analyst.\n"
        "Your mission is to TRIAGE and MITIGATE incoming security incidents.\n"
        "Workflow:\n"
        "1. investigate(query) - Query threat intel playbooks.\n"
        "2. mitigate(team, priority, status) - Update containment unit and severity.\n"
        "3. report(text) - Draft the CISO incident report.\n"
        "4. submit() - Close the incident.\n"
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "investigate",
                "description": "Search the threat intelligence database for playbooks.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mitigate",
                "description": "Deploy countermeasures. Update unit, severity, and status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "team": {"type": "string", "enum": ["security", "it_support", "billing", "product", "hardware", "hr"]},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical", "urgent"]},
                        "status": {"type": "string", "enum": ["open", "in_progress", "resolved", "escalated"]}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "report",
                "description": "Draft an incident report.",
                "parameters": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "submit",
                "description": "Close incident when mitigation is finalized.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    ]

    llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy"))
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"CURRENT_ALERT: {incident}"}
    ]

    score = 0.01
    for step in range(MAX_STEPS := 10):
        time.sleep(0.5)
        try:
            response = llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
        except Exception as e:
            print(f"OpenAI error: {e}")
            return 0.01

        msg = response.choices[0].message
        messages.append(msg)

        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                if name == "investigate":
                    action = SentinelAction(action_type="investigate", search_query=args.get("query"))
                elif name == "mitigate":
                    action = SentinelAction(
                        action_type="mitigate", 
                        team=args.get("team"), 
                        priority=args.get("priority"),
                        status=args.get("status")
                    )
                elif name == "report":
                    action = SentinelAction(action_type="report", reply_text=args.get("text"))
                elif name == "submit":
                    action = SentinelAction(action_type="submit")
                else:
                    continue

                try:
                    res = client.step(action)
                    score += res.reward
                    obs = res.observation
                    content = obs.system_message + ("\nINTEL: " + obs.kb_search_results if obs.kb_search_results else "")
                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": content})
                    if res.done:
                        # Score is the reward at done — already clamped to (0.01, 0.99)
                        return float(max(0.01, min(0.99, res.reward)))
                except Exception as e:
                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(e)})

        else:
            messages.append({"role": "user", "content": "Keep investigating until the threat is neutralized, then submit()."})

    # Fallback: clamp accumulated score strictly between 0 and 1
    return float(max(0.01, min(0.99, score)))

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:7860")
    args = p.parse_args()

    print(f"Establishing Uplink to {args.url}...")
    try:
        with SentinelEnv(base_url=args.url).sync() as client:
            for lvl in ["easy", "medium", "hard"]:
                print(f"--- DEFCON {lvl.upper()} DRILL ---")
                s = run_eval(client, lvl)
                print(f"Maneuver Efficiency: {s:.2f}\n")
    except Exception as e:
        print(f"Uplink Failure: {e}")

if __name__ == "__main__":
    main()
