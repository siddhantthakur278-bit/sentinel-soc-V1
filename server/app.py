"""
FastAPI application for the Support Ticket Triage Environment.
This module creates an HTTP server that exposes the SupportTicketTriageEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.
Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions
Usage:
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4
    python -m server.app
"""
try:
    from openenv.core.env_server.http_server import create_app
    import gradio as gr
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    import os
    import json
    import time
    from typing import Dict, Any
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv and gradio are required. Install dependencies with '\n    uv sync\n'"
    ) from e
try:
    from ..models import SupportTicketTriageAction, SupportTicketTriageObservation
    from .support_ticket_triage_environment import SupportTicketTriageEnvironment
except ImportError:
    from models import SupportTicketTriageAction, SupportTicketTriageObservation
    from server.support_ticket_triage_environment import SupportTicketTriageEnvironment
base_app = create_app(
    SupportTicketTriageEnvironment,
    SupportTicketTriageAction,
    SupportTicketTriageObservation,
    env_name="support_ticket_triage",
    max_concurrent_envs=10,
)

# --- Final Strategic Operational Dashboard UI ---
def create_ui():
    env = SupportTicketTriageEnvironment()
    
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    body, .gradio-container { 
        background-color: #f3f5f7 !important; 
        font-family: 'Inter', -apple-system, system-ui, sans-serif !important; 
        color: #183247 !important;
    }
    
    .main-card {
        background: white !important;
        border: 1px solid #ebeef0;
        border-radius: 8px;
        box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05);
        padding: 24px;
    }
    
    .sidebar-card {
        background: #ffffff !important;
        border: 1px solid #ebeef0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    .header-bar { 
        background: #183247 !important; 
        color: white !important; 
        padding: 12px 24px;
        border-radius: 0 0 0 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 24px;
    }
    .header-bar h1 { color: white !important; margin: 0; font-size: 1.25rem; font-weight: 600; }
    
    .label-tag {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #475d68;
        margin-bottom: 4px;
        display: block;
    }
    
    /* Freddy AI Styles */
    .freddy-copilot {
        background: linear-gradient(135deg, #f0faff 0%, #ffffff 100%);
        border: 1px solid #cceeff;
        border-left: 4px solid #2cc5d2;
        border-radius: 8px;
        padding: 16px;
        margin-top: 12px;
    }
    
    .freddy-avatar {
        width: 48px;
        height: 48px;
        margin-bottom: 8px;
    }
    
    .kb-module { 
        background: #f9fafb; 
        border: 1px dashed #d1d5db; 
        padding: 12px; 
        border-radius: 6px; 
        font-size: 0.875rem; 
        max-height: 250px; 
        overflow-y: auto; 
    }
    
    button.primary { background: #007bff !important; border: none !important; font-weight: 600 !important; color: white !important; transition: all 0.2s; }
    button.primary:hover { background: #0062cc !important; box-shadow: 0 2px 8px rgba(0,123,255,0.3); }
    
    button.secondary { background: white !important; border: 1px solid #d1d5db !important; color: #183247 !important; }
    button.secondary:hover { background: #f9fafb !important; }

    .ticket-meta { font-size: 0.85rem; color: #475d68; }
    .status-badge { display: inline-block; padding: 4px 12px; border-radius: 16px; font-size: 0.75rem; font-weight: 600; }
    
    /* Gradio overrides */
    div.svelte-1mwv56b { color: #183247 !important; }
    .gradio-button { border-radius: 6px !important; }
    textarea, input, select { border-radius: 6px !important; border-color: #d1d5db !important; }
    """

    with gr.Blocks(title="Freshdesk | AI Service Desk") as demo:
        # 1. Navbar
        with gr.Row(elem_classes="header-bar"):
            with gr.Column(scale=4):
                gr.HTML('<div style="display: flex; align-items: center; gap: 16px;">'
                        '<img src="/logo.png" style="height: 48px; border-radius: 4px;">'
                        '<div><h1 style="margin: 0; line-height: 1.2;">FreshTriage</h1>'
                        '<p style="margin: 0; font-size: 0.75rem; color: #7ee787;">● SYSTEM REASONING ACTIVE</p></div></div>')
            with gr.Column(scale=1):
                gr.HTML('<div style="text-align: right; font-size: 0.85rem; opacity: 0.8;">SESSION: META-HACK-V1<br>UPLINK: STABLE</div>')

        # 2. Main Content
        with gr.Row():
            # LEFT: Ticket Context & Triage
            with gr.Column(scale=1):
                with gr.Column(elem_classes="sidebar-card"):
                    gr.Markdown("### ⚙️ Session Settings")
                    task_type = gr.Dropdown(["easy", "medium", "hard"], label="LEVEL", value="easy")
                    reset_btn = gr.Button("Initialize Ticket", variant="primary", scale=1)
                    auto_btn = gr.Button("🤖 RUN AI AUTO-TRIAGE", variant="primary")
                
                with gr.Column(elem_classes="sidebar-card"):
                    gr.Markdown("### 📍 Triage Details")
                    team_sel = gr.Dropdown(["billing", "it_support", "product", "hardware", "security", "hr"], label="ASSIGN TO")
                    prio_sel = gr.Dropdown(["low", "medium", "high", "critical", "urgent"], label="PRIORITY")
                    stat_sel = gr.Dropdown(["open", "in_progress", "resolved", "escalated"], label="STATUS")
                    triage_btn = gr.Button("Update Triage", variant="secondary")

                with gr.Column(elem_classes="sidebar-card"):
                    gr.Markdown("### 📊 Metrics")
                    reward_disp = gr.Number(value=0.0, label="EPISODE SCORE", precision=3)
                    step_gauge = gr.Label(value="10/10", label="TURNS REMAINING")

            # MIDDLE: Conversation Area
            with gr.Column(scale=2, elem_classes="main-card"):
                gr.Markdown("## 🎟️ Active Ticket Details")
                
                with gr.Row():
                    sentiment_badge = gr.Label(value="NEUTRAL 😐", label="CUSTOMER SENTIMENT")
                    sla_timer = gr.Label(value="24h 00m", label="SLA BREACH CLOCK")
                    tier_badge = gr.Label(value="Standard", label="CUSTOMER TIER")
                    
                ticket_box = gr.Textbox(label="CUSTOMER REQUEST", interactive=False, lines=5)
                
                gr.HTML("<hr style='border: 0; border-top: 1px solid #ebeef0; margin: 20px 0;'>")
                
                gr.Markdown("### ⚡ Quick Macros")
                with gr.Row():
                    macro_refund = gr.Button("💰 Issue Refund", size="sm")
                    macro_reset = gr.Button("🔑 Password Reset", size="sm")
                    macro_escalate = gr.Button("🚨 Escalate to L2", size="sm", variant="stop")
                    
                gr.Markdown("### ✉️ Response Draft")
                reply_text = gr.Textbox(placeholder="Type your resolution here...", label="DRAFT REPLY", lines=4)
                
                with gr.Row():
                    save_btn = gr.Button("Save Draft", variant="secondary")
                    submit_btn = gr.Button("Submit & Close Ticket", variant="primary")
                
                sys_msg = gr.Markdown("*System messages will appear here after actions.*")

            # RIGHT: AI Copilot & Insights
            with gr.Column(scale=1):
                with gr.Column(elem_classes="freddy-copilot"):
                    gr.Markdown("### ✨ AI Copilot Insights")
                    suggestion_box = gr.Label(value="Analyzing...", label="PREDICTED CATEGORY")
                    
                    gr.HTML("<hr style='border: 0; border-top: 1px solid #cceeff; margin: 12px 0;'>")
                    gr.Markdown("#### 🧠 Reasoning Engine")
                    reasoning_log = gr.Textbox(label="INTERNAL THOUGHTS", interactive=False, placeholder="AI is preparing to analyze...", lines=5)
                    
                with gr.Column(elem_classes="sidebar-card"):
                    gr.Markdown("### 📜 Performance Audit")
                    history_table = gr.Dataframe(
                        headers=["TS", "Lvl", "Score"], 
                        datatype=["str", "str", "number"], 
                        value=[], 
                        interactive=False
                    )
                    score_plot = gr.LinePlot(
                        x="Run", y="Score", title="Reward Analytics", tooltip=["Run", "Score", "Lvl"]
                    )

                with gr.Column(elem_classes="sidebar-card"):
                    gr.Markdown("### 🔍 KB Search")
                    search_query = gr.Textbox(placeholder="Query...", label="INTEL SEARCH")
                    search_btn = gr.Button("Search", variant="secondary")
                    kb_box = gr.Markdown("*Research results...*", elem_classes="kb-module")

        # 3. State & Logic
        log_state = gr.State([])
        total_reward = gr.State(0.0)
        history_state = gr.State([])
        env_state = gr.State(None)

        def update_ui(obs, env, logs, current_total, history):
            kb_content = obs.kb_search_results
            if kb_content and kb_content.strip():
                clean_kb = kb_content.replace("\n", "<br>").replace("\\n", "<br>")
                kb_md = f'<div class="kb-module"><b>RETRIEVED INTEL:</b><br>{clean_kb}</div>'
            else:
                kb_md = "*No research data available.*"
            
            # Advanced Suggestion & Reasoning Logic
            suggestion = "UNCERTAIN"
            thought = "Scanning ticket metadata... "
            t = obs.current_ticket.lower()
            words = t.split()
            
            # --- Zendesk-style Sentiment & SLA Tracking ---
            sentiment = "NEUTRAL 😐"
            if any(k in t for k in ["urgent", "angry", "unacceptable", "breach", "fail", "broken", "critical", "dropping"]):
                sentiment = "FRUSTRATED 😡"
            elif any(k in t for k in ["please", "thank", "wondering", "help", "new"]):
                sentiment = "POLITE 😌"
                
            sla = "2h 15m (WARNING)" if sentiment == "FRUSTRATED 😡" else "24h 00m"
            tier = "Enterprise" if any(k in t for k in ["production", "breach", "invoice", "payroll"]) else "Standard"

            if any(k in t for k in ["payment", "invoice", "refund"]): 
                suggestion = "BILLING"
                thought += "Detected transaction-related keywords. Checking knowledge base for billing policies..."
            elif any(k in words or k in t for k in ["login", "password", "vpn"]): 
                suggestion = "IT_SUPPORT"
                thought += "Access management symbols identified. This looks like a credential or connectivity issue."
            elif any(k in t for k in ["bug", "feature", "ui", "crash"]): 
                suggestion = "PRODUCT"
                thought += "Product feedback or technical bug detected. Triage to product engineering."
            elif any(k in t for k in ["monitor", "keyboard", "laptop"]): 
                suggestion = "HARDWARE"
                thought += "Physical equipment mentioned. Verifying warranty and hardware support team availability."
            elif any(k in t for k in ["phishing", "breach", "security"]): 
                suggestion = "SECURITY"
                thought += "CRITICAL: Security incident keywords found. Escalating to SecOps for immediate review."
            else:
                thought += "Initial reading complete. Preparing to search KB for more context..."

            reward = getattr(obs, 'reward', 0.0)
            new_total = current_total + reward
            new_logs = logs + [f"[{obs.system_message}]"]
            steps_left = 10 - getattr(obs, 'step_count', 0)
            
            new_history = history
            if obs.done:
                from datetime import datetime
                ts = datetime.now().strftime("%H:%M:%S")
                task_lv = env.task_level.upper() if env and env.task_level else "N/A"
                new_history = [[ts, task_lv, round(new_total, 3)]] + history
            
            import pandas as pd
            if new_history:
                rev = new_history[::-1]
                plot_df = pd.DataFrame({
                    "Run": [str(i+1) for i in range(len(rev))],
                    "Score": [row[2] for row in rev],
                    "Lvl": [row[1] for row in rev]
                })
            else:
                plot_df = pd.DataFrame(columns=["Run", "Score", "Lvl"])

            return {
                ticket_box: obs.current_ticket,
                sentiment_badge: sentiment,
                sla_timer: sla,
                tier_badge: tier,
                kb_box: kb_md,
                suggestion_box: suggestion,
                reasoning_log: thought,
                step_gauge: f"Quota: {steps_left}/10 Actions Left",
                reward_disp: new_total,
                sys_msg: f"**Status:** {obs.system_message}",
                total_reward: new_total,
                history_table: new_history,
                score_plot: plot_df,
                history_state: new_history,
                team_sel: obs.ticket_team if obs.ticket_team and obs.ticket_team != "unassigned" else None,
                prio_sel: obs.ticket_priority if obs.ticket_priority and obs.ticket_priority != "unassigned" else None,
                stat_sel: obs.ticket_status if obs.ticket_status and obs.ticket_status != "unassigned" else "open",
                reply_text: obs.draft_reply if obs.draft_reply else "",
                search_query: ""
            }

        def on_reset(level, history, env):
            if env is None: env = SupportTicketTriageEnvironment()
            env.reset()
            obs = env.step(SupportTicketTriageAction(action_type="start_task", task_level=level))
            result = update_ui(obs, env, [f"SESSION_START: {level.upper()}"], 0.0, history)
            result[env_state] = env
            return result

        def on_search(query, logs, current_total, history, env):
            if env is None: return {sys_msg: "Please initialize a session first."}
            obs = env.step(SupportTicketTriageAction(action_type="search_kb", search_query=query))
            result = update_ui(obs, env, logs + [f"SEARCH: {query}"], current_total, history)
            result[env_state] = env
            return result

        def on_triage(team, prio, stat, logs, current_total, history, env):
            if env is None: return {sys_msg: "Please initialize a session first."}
            obs = env.step(SupportTicketTriageAction(action_type="update_ticket", team=team, priority=prio, status=stat))
            result = update_ui(obs, env, logs + [f"ROUTING: {team or 'N/A'}"], current_total, history)
            result[env_state] = env
            return result

        def on_reply(text, logs, current_total, history, env):
            if env is None: return {sys_msg: "Please initialize a session first."}
            obs = env.step(SupportTicketTriageAction(action_type="reply", reply_text=text))
            result = update_ui(obs, env, logs + ["BUFFERED: REPLY_DRAFT"], current_total, history)
            result[env_state] = env
            return result

        def on_submit(logs, current_total, history, env):
            if env is None: return {sys_msg: "Please initialize a session first."}
            obs = env.step(SupportTicketTriageAction(action_type="submit"))
            obs.done = True
            result = update_ui(obs, env, logs + ["BROADCAST_COMPLETE"], current_total, history)
            result[env_state] = env
            return result

        # 4. Agentic Logic (Native UI Agent)
        def on_auto_triage(logs, current_total, history, env):
            if env is None: yield {sys_msg: "Please initialize a session first."}; return
            
            from openai import OpenAI
            client = OpenAI(base_url=os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1"), api_key=os.getenv("HF_TOKEN"))
            model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

            # Initial Thinking
            yield {reasoning_log: "🤖 AI AGENT ACTIVATED. Analyzing ticket...", sys_msg: "**Status:** AI Agent taking control..."}
            
            for _ in range(8):  # Max steps
                state = env._get_observation("AI Thinking...")
                prompt = f"Ticket: {state.current_ticket}\nKB: {state.kb_search_results}\nStatus: {state.ticket_status}\nTeam: {state.ticket_team}\nDraft: {state.draft_reply}"
                
                try:
                    res = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a support agent. Output ONLY valid JSON with THIS EXACT SCHEMA: {\"thinking\": \"...\", \"action\": {\"action_type\": \"...\", \"reply_text\": \"...\", \"team\": \"...\", \"priority\": \"...\", \"status\": \"...\", \"search_query\": \"...\"}}.\n\nSTRICT RULES:\n- Use ONLY these action_types: search_kb, update_ticket, reply, submit.\n- For triage, 'team' MUST be: billing, it_support, product, hardware, security, or hr.\n- For triage, 'priority' MUST be: low, medium, high, critical, or urgent.\n- For messages, use the key 'reply_text' (NOT 'message').\n- Output ONLY JSON. No markdown."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
                    raw_content = res.choices[0].message.content
                    print(f"DEBUG: AI RESPONSE -> {raw_content}") # For terminal debugging
                    data = json.loads(raw_content)
                    thinking = data.get("thinking", data.get("think", "Analyzing..."))
                    action_data = data.get("action", data) # Fallback to top level if "action" key missing
                    
                    # --- NUCLEAR SANITIZATION ---
                    # 1. Force convert any "message" or "response" to "reply_text"
                    for key in ["message", "response", "msg", "draft", "text"]:
                        if key in action_data and "reply_text" not in action_data:
                            action_data["reply_text"] = action_data.pop(key)
                    
                    # 2. Strict Filter: Allow ONLY valid keys, Drop empty strings, Drop 'unassigned'
                    allowed = {"action_type", "task_level", "search_query", "priority", "team", "status", "reply_text"}
                    sanitized = {str(k): v for k, v in action_data.items() if k in allowed and v is not None and str(v).strip() != "" and str(v).lower() != "unassigned"}
                    
                    # 3. Default fixes
                    if "action_type" not in sanitized: 
                        sanitized["action_type"] = "search_kb"
                    elif sanitized["action_type"] == "triage":
                        sanitized["action_type"] = "update_ticket"
                    elif sanitized["action_type"] not in ["search_kb", "update_ticket", "reply", "submit", "start_task"]:
                        sanitized["action_type"] = "update_ticket"
                        
                    if not sanitized.get("search_query") and sanitized["action_type"] == "search_kb":
                        sanitized["search_query"] = "support"
                    
                    if sanitized.get("status") == "closed":
                        sanitized["status"] = "resolved"
                        
                    # 4. Strict Literal Enum Enforcement
                    if "status" in sanitized and sanitized["status"] not in {"open", "in_progress", "resolved", "escalated"}:
                        sanitized.pop("status")
                    if "priority" in sanitized and sanitized["priority"] not in {"low", "medium", "high", "critical", "urgent"}:
                        sanitized.pop("priority")
                    if "team" in sanitized and sanitized["team"] not in {"billing", "it_support", "product", "hardware", "security", "hr"}:
                        sanitized.pop("team")
                    
                    # Yield "Thinking" state
                    yield {reasoning_log: thinking, sys_msg: f"**Status:** {thinking[:100]}..."}
                    import time; time.sleep(1.0) 

                    action_obj = SupportTicketTriageAction(**sanitized)
                    obs = env.step(action_obj)
                    
                    # Update all UI components live
                    ui_update = update_ui(obs, env, logs + [f"AI: {action_obj.action_type}"], current_total, history)
                    ui_update[reasoning_log] = thinking
                    
                    # Mirror the Agent's specific actions directly onto the UI inputs:
                    if action_obj.action_type == "search_kb" and action_obj.search_query:
                        ui_update[search_query] = action_obj.search_query
                    if action_obj.action_type == "reply" and action_obj.reply_text:
                        ui_update[reply_text] = action_obj.reply_text
                    if action_obj.action_type == "update_ticket":
                        if action_obj.team and action_obj.team != "unassigned": ui_update[team_sel] = action_obj.team
                        if action_obj.priority and action_obj.priority != "unassigned": ui_update[prio_sel] = action_obj.priority
                        if action_obj.status and action_obj.status != "unassigned": ui_update[stat_sel] = action_obj.status
                        
                    yield ui_update
                    
                    current_total = ui_update[reward_disp]
                    
                    if obs.done: break
                    time.sleep(0.8)
                except Exception as e:
                    yield {sys_msg: f"**AI ERROR:** {str(e)}"}
                    break

        # 5. Wire Uplinks
        ALL_OUTPUTS = [ticket_box, kb_box, suggestion_box, reasoning_log, step_gauge, reward_disp, sys_msg, total_reward, history_table, history_state, team_sel, prio_sel, stat_sel, reply_text, search_query, score_plot, sentiment_badge, sla_timer, tier_badge]
        
        # Add the Auto-Triage Button to the UI column (sidebar)
        with gr.Column(scale=1): 
            pass

        macro_refund.click(lambda: "I have initiated a full refund for your recent transaction. It will appear on your statement in 3-5 business days.", None, reply_text)
        macro_reset.click(lambda: "Please click the 'Forgot Password' link on the login page to securely reset your credentials and restore access to your account.", None, reply_text)
        macro_escalate.click(lambda: "escalated", None, stat_sel)

        reset_btn.click(on_reset, inputs=[task_type, history_state, env_state], outputs=ALL_OUTPUTS + [env_state])
        search_btn.click(on_search, inputs=[search_query, log_state, total_reward, history_state, env_state], outputs=ALL_OUTPUTS + [env_state])
        triage_btn.click(on_triage, inputs=[team_sel, prio_sel, stat_sel, log_state, total_reward, history_state, env_state], outputs=ALL_OUTPUTS + [env_state])
        save_btn.click(on_reply, inputs=[reply_text, log_state, total_reward, history_state, env_state], outputs=ALL_OUTPUTS + [env_state])
        submit_btn.click(on_submit, inputs=[log_state, total_reward, history_state, env_state], outputs=ALL_OUTPUTS + [env_state])
        auto_btn.click(on_auto_triage, inputs=[log_state, total_reward, history_state, env_state], outputs=ALL_OUTPUTS)

    return demo

# --- Asset Route: inline SVG logo (no binary file needed in repo) ---
from fastapi.responses import Response as FastAPIResponse

@base_app.get("/logo.png")
async def get_logo():
    """Serve logo — try local file first, fall back to inline SVG."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(p):
        return FileResponse(p)
    # Inline SVG fallback — no binary file required in repo
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="48" viewBox="0 0 120 48">'
        '<rect width="120" height="48" rx="8" fill="#2cc5d2"/>'
        '<text x="60" y="30" font-family="Inter,sans-serif" font-size="14" font-weight="700" '
        'fill="#ffffff" text-anchor="middle" dominant-baseline="middle">FreshTriage</text>'
        '</svg>'
    )
    return FastAPIResponse(content=svg, media_type="image/svg+xml")

# Mount Gradio into the FastAPI app
app = gr.mount_gradio_app(base_app, create_ui(), path="/")
def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution via uv run or python -m.
    This function enables running the server without Docker:
        uv run --project . server
        uv run --project . server --port 8001
        python -m support_ticket_triage.server.app
    Args:
        host: Host address to bind to (default: "0.0.0.0")
        port: Port number to listen on (default: 8000)
    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn support_ticket_triage.server.app:app --workers 4
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)
if __name__ == "__main__":
    main()
