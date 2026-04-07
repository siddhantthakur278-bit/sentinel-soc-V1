import os
import time
import json
try:
    from openai import OpenAI
except ImportError:
    print("Please install openai: pip install openai")
    exit(1)
from client import SupportTicketTriageEnv
from models import SupportTicketTriageAction
def run_eval(client, task_level):
    result = client.reset()
    start_action = SupportTicketTriageAction(action_type="start_task", task_level=task_level)
    result = client.step(start_action)
    ticket = result.observation.current_ticket
    system_prompt = (
        "You are an AI Support Ticket Triage bot.\\n"
        "Your job is to strictly follow this workflow:\\n"
        "1. Read the ticket.\\n"
        "2. If the issue requires specialized knowledge, use search_kb(query)\\n"
        "3. Use update_ticket(team, priority, status) to map the ticket.\\n"
        "4. Use reply(text) to draft a response. Include the actual solution from the KB if you searched for one, or directly address their concern with relevant keywords.\\n"
        "5. Call submit() when you are completely finished.\\n"
        "Allowed teams: billing, it_support, product, hardware, security, hr.\\n"
        "Allowed priorities: low, medium, high, critical, urgent.\\n"
        "Allowed statuses: open, in_progress, resolved, escalated."
    )
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_kb",
                "description": "Search the knowledge base for a short simple query",
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
                "name": "update_ticket",
                "description": "Update ticket fields. All fields are optional but you should provide what you know.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "team": {"type": "string", "enum": ["billing", "it_support", "product", "hardware", "security", "hr"]},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical", "urgent"]},
                        "status": {"type": "string", "enum": ["open", "in_progress", "resolved", "escalated"]}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "reply",
                "description": "Draft a reply to the customer.",
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
                "description": "Submit task when complete",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    ]
    llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy"))
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Current ticket: {ticket}"}
    ]
    score = 0.0
    for step in range(12):  # fallback limit
        time.sleep(0.5)
        try:
            response = llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
        except Exception as e:
            print(f"OpenAI error (are you missing OPENAI_API_KEY?): {e}")
            return 0.0
        msg = response.choices[0].message
        messages.append(msg)
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = {}
                if tool_call.function.arguments:
                    args = json.loads(tool_call.function.arguments)
                if name == "search_kb":
                    action = SupportTicketTriageAction(action_type="search_kb", search_query=args.get("query"))
                elif name == "update_ticket":
                    action = SupportTicketTriageAction(
                        action_type="update_ticket", 
                        team=args.get("team"), 
                        priority=args.get("priority"),
                        status=args.get("status")
                    )
                elif name == "reply":
                    action = SupportTicketTriageAction(action_type="reply", reply_text=args.get("text"))
                elif name == "submit":
                    action = SupportTicketTriageAction(action_type="submit")
                else:
                    print(f"Unknown action {name}")
                    continue
                try:
                    result = client.step(action)
                    score += result.reward
                except Exception as e:
                    print(f"Env step error: {e}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(e)
                    })
                    continue
                sys_msg = result.observation.system_message
                kb_res = result.observation.kb_search_results
                content = sys_msg + ("\nKB RESULTS: " + kb_res if kb_res else "")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": content
                })
                if result.done:
                    return score
        else:
            messages.append({"role": "user", "content": "Keep going and complete the task. You must use tools to take actions and finally submit()."})
    return score
def main():
    """Main entry point for baseline evaluation."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:7860")
    args = parser.parse_args()
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set. OpenAI API calls will likely fail.")
    
    print(f"Connecting to environment at {args.url}...")
    try:
        with SupportTicketTriageEnv(base_url=args.url).sync() as client:
            print("--- Running Baseline on Easy Task ---")
            easy_score = run_eval(client, "easy")
            print(f"Score: {easy_score}\n")
            print("--- Running Baseline on Medium Task ---")
            medium_score = run_eval(client, "medium")
            print(f"Score: {medium_score}\n")
            print("--- Running Baseline on Hard Task ---")
            hard_score = run_eval(client, "hard")
            print(f"Score: {hard_score}\n")
            print(f"Total Baseline Score: {easy_score + medium_score + hard_score} / 3.0")
    except Exception as e:
        print(f"Could not connect to environment: {e}")
        print("Make sure the environment server is running locally on port 7860 before executing this baseline.")

if __name__ == "__main__":
    main()
