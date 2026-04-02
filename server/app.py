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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@500&display=swap');
    
    .gradio-container { 
        background: url('/background.png') no-repeat center fixed !important; 
        background-size: cover !important;
        font-family: 'Inter', sans-serif !important; 
    }
    
    .col-card { 
        background: rgba(13, 17, 23, 0.8) !important; 
        backdrop-filter: blur(12px); 
        border: 1px solid rgba(88, 166, 255, 0.2); 
        border-radius: 12px; 
        padding: 12px; 
        height: 100%; 
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.7);
    }
    
    .header-bar { border-bottom: 1px solid rgba(88, 166, 255, 0.3); margin-bottom: 16px; padding-bottom: 4px; }
    .log-viewer { font-family: 'JetBrains Mono', monospace; font-size: 0.75em; background: rgba(1, 4, 9, 0.7) !important; color: #7ee787 !important; border: 1px solid #30363d !important; }
    .kb-module { background: rgba(1, 4, 9, 0.5); border: 1px solid rgba(240, 136, 62, 0.4); border-left: 4px solid #f0883e; padding: 10px; border-radius: 4px; font-size: 0.85em; height: 180px; overflow-y: auto; }
    .tiny-label { font-size: 0.7em; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }
    button.primary { background: #238636 !important; border: none !important; font-size: 0.9em !important; box-shadow: 0 0 10px rgba(35, 134, 54, 0.3); }
    button.stop { background: #da3633 !important; border: none !important; box-shadow: 0 0 15px rgba(218, 54, 51, 0.3); }
    
    /* Input Visibility */
    input, select, textarea { background: rgba(1, 4, 9, 0.6) !important; color: #e6edf3 !important; border: 1px solid #30363d !important; }
    label { color: #58a6ff !important; font-weight: 700 !important; }
    """

    with gr.Blocks(theme=gr.themes.Default(spacing_size="sm", radius_size="sm"), css=css) as demo:
        # 1. Header Section
        with gr.Row(elem_classes="header-bar"):
            with gr.Column(scale=3):
                gr.Markdown("# 🛸 AGENTIC TRIAGE OS")
                gr.Markdown("ENV: SUPPORT_V1-ALPHA | UPLINK: STABLE", elem_classes="tiny-label")
            with gr.Column(scale=1):
                gr.HTML('<div style="text-align: right; font-family: monospace; font-size: 0.8em;"><span style="color: #3fb950;">● SYSTEM_READY</span><br><span style="color: #8b949e;">ID: TI-992-DELTA</span></div>')

        # 2. Main 3-Column Dash
        with gr.Row(equal_height=True):
            # LEFT: Control Deck
            with gr.Column(scale=1, elem_classes="col-card"):
                gr.Markdown("### 🕹️ CONTROL DECK")
                with gr.Group():
                    task_type = gr.Dropdown(["easy", "medium", "hard"], label="MISSION DIFFICULTY", value="easy")
                    reset_btn = gr.Button("🚀 INITIALIZE SESSION", variant="primary")
                
                gr.Markdown("---")
                with gr.Accordion("🛠️ OPERATIONAL WORKFLOW", open=True):
                    with gr.Group():
                        search_query = gr.Textbox(placeholder="Enter search parameters...", label="INTEL QUERY", lines=1)
                        search_btn = gr.Button("SEARCH DATABASE", size="sm")
                    
                    gr.Markdown("---")
                    with gr.Group():
                        team_sel = gr.Dropdown(["billing", "it_support", "product", "hardware"], label="DEPT")
                        prio_sel = gr.Dropdown(["low", "medium", "high", "critical"], label="PRIO")
                        stat_sel = gr.Dropdown(["open", "in_progress", "resolved"], label="STATUS")
                        triage_btn = gr.Button("UPDATE FIELDS", size="sm")
                    
                    gr.Markdown("---")
                    with gr.Group():
                        reply_text = gr.Textbox(placeholder="Draft resolution...", label="REPLY COMPOSER", lines=2)
                        reply_btn = gr.Button("CACHE DRAFT", size="sm")

            # CENTER: Active Workspace
            with gr.Column(scale=2, elem_classes="col-card"):
                with gr.Row():
                    gr.Markdown("### 📋 ACTIVE WORKSPACE")
                    step_gauge = gr.Label(value="10/10", label="STEPS REMAINING", scale=0)
                
                ticket_box = gr.Textbox(label="INCOMING DATA STREAM", interactive=False, lines=4)
                
                with gr.Row():
                    with gr.Column(scale=1):
                        suggestion_box = gr.Label(value="NO DATA", label="AI SUGGESTION")
                    with gr.Column(scale=2):
                        kb_box = gr.Markdown("*Research data will appear here...*", elem_classes="kb-module")
                
                gr.Markdown("---")
                submit_btn = gr.Button("💎 BROADCAST SOLUTION", variant="stop", size="lg")
                sys_msg = gr.Textbox(label="SYSTEM TELEMETRY FEEDBACK", interactive=False, container=False)

            # RIGHT: Analytics & Audit
            with gr.Column(scale=1, elem_classes="col-card"):
                gr.Markdown("### 📊 ANALYTICS")
                with gr.Group():
                    reward_disp = gr.Number(value=0.0, label="EPISODE SCORE", precision=3)
                    with gr.Row():
                        team_disp = gr.Label(value="N/A", label="CURRENT DEPT", scale=1)
                        prio_disp = gr.Label(value="N/A", label="CURRENT PRIO", scale=1)
                
                gr.Markdown("---")
                gr.Markdown("### 📜 SESSION ARCHIVE")
                history_table = gr.Dataframe(headers=["#", "Lvl", "Score"], datatype=["str", "str", "number"], value=[])
                
                gr.Markdown("---")
                action_log_box = gr.Textbox(show_label=False, lines=10, interactive=False, elem_classes="log-viewer")

        # 3. State & Logic
        log_state = gr.State([])
        total_reward = gr.State(0.0)
        history_state = gr.State([])

        def update_ui(obs, logs, current_total, history):
            kb_content = obs.kb_search_results
            if kb_content and kb_content.strip():
                clean_kb = kb_content.replace("\\n", "<br>")
                kb_md = f'<div class="kb-module"><b>INTEL DATA:</b><br>{clean_kb}</div>'
            else:
                kb_md = "*No research data available.*"
            
            # AI Suggestion Logic (Advanced Keyword Match)
            suggestion = "UNCERTAIN"
            t = obs.current_ticket.lower()
            # Normalize ticket text (remove punctuation for better matching)
            t_clean = "".join(char if char.isalnum() or char.isspace() else " " for char in t)
            words = t_clean.split()
            
            if any(k in t for k in ["payment", "invoice", "refund", "subscription", "price", "billing"]): suggestion = "BILLING"
            elif any(k in words or k in t for k in ["login", "password", "vpn", "access", "wi-fi", "account", "2fa", "locked"]): suggestion = "IT_SUPPORT"
            elif any(k in t for k in ["bug", "feature", "ui", "ux", "crash", "picture", "avatar", "profile", "settings"]): suggestion = "PRODUCT"
            elif any(k in t for k in ["hardware", "monitor", "cable", "mouse", "keyboard", "screen", "laptop"]): suggestion = "HARDWARE"

            reward = getattr(obs, 'reward', 0.0)
            new_total = current_total + reward
            new_logs = logs + [f"[{obs.system_message}]"]
            
            # Step Budget calculation
            steps_left = 10 - getattr(obs, 'step_count', 0)
            
            # Update History if done
            new_history = history
            if obs.done:
                new_history = history + [[str(len(history)+1), env.task_level or "N/A", round(new_total, 3)]]

            return {
                ticket_box: obs.current_ticket,
                kb_box: kb_md,
                suggestion_box: suggestion,
                step_gauge: f"CAPACITY: {steps_left}/10 STEPS",
                team_disp: obs.ticket_team.upper() if obs.ticket_team else "N/A",
                prio_disp: obs.ticket_priority.upper() if obs.ticket_priority else "N/A",
                reward_disp: new_total,
                sys_msg: obs.system_message,
                action_log_box: "\n".join([f"> {L}" for L in new_logs[-12:]]),
                log_state: new_logs,
                total_reward: new_total,
                history_table: new_history,
                history_state: new_history
            }

        def on_reset(level, history):
            env.reset()
            obs = env.step(SupportTicketTriageAction(action_type="start_task", task_level=level))
            return update_ui(obs, [f"SESSION_START: {level.upper()}"], 0.0, history)

        def on_search(query, logs, current_total, history):
            obs = env.step(SupportTicketTriageAction(action_type="search_kb", search_query=query))
            return update_ui(obs, logs + [f"SEARCH: {query}"], current_total, history)

        def on_triage(team, prio, stat, logs, current_total, history):
            obs = env.step(SupportTicketTriageAction(action_type="update_ticket", team=team, priority=prio, status=stat))
            return update_ui(obs, logs + [f"ROUTING: {team or 'N/A'}"], current_total, history)

        def on_reply(text, logs, current_total, history):
            obs = env.step(SupportTicketTriageAction(action_type="reply", reply_text=text))
            return update_ui(obs, logs + ["BUFFERED: REPLY_DRAFT"], current_total, history)

        def on_submit(logs, current_total, history):
            obs = env.step(SupportTicketTriageAction(action_type="submit"))
            # Submit makes it done
            obs.done = True
            return update_ui(obs, logs + ["BROADCAST_COMPLETE"], current_total, history)

        # 4. Wire Uplinks
        reset_btn.click(on_reset, inputs=[task_type, history_state], outputs=[ticket_box, kb_box, suggestion_box, step_gauge, team_disp, prio_disp, reward_disp, sys_msg, action_log_box, log_state, total_reward, history_table, history_state])
        search_btn.click(on_search, inputs=[search_query, log_state, total_reward, history_state], outputs=[ticket_box, kb_box, suggestion_box, step_gauge, team_disp, prio_disp, reward_disp, sys_msg, action_log_box, log_state, total_reward, history_table, history_state])
        triage_btn.click(on_triage, inputs=[team_sel, prio_sel, stat_sel, log_state, total_reward, history_state], outputs=[ticket_box, kb_box, suggestion_box, step_gauge, team_disp, prio_disp, reward_disp, sys_msg, action_log_box, log_state, total_reward, history_table, history_state])
        reply_btn.click(on_reply, inputs=[reply_text, log_state, total_reward, history_state], outputs=[ticket_box, kb_box, suggestion_box, step_gauge, team_disp, prio_disp, reward_disp, sys_msg, action_log_box, log_state, total_reward, history_table, history_state])
        submit_btn.click(on_submit, inputs=[log_state, total_reward, history_state], outputs=[ticket_box, kb_box, suggestion_box, step_gauge, team_disp, prio_disp, reward_disp, sys_msg, action_log_box, log_state, total_reward, history_table, history_state])

    return demo

# --- Asset Route ---
@base_app.get("/background.png")
async def get_background():
    # Final, most robust path resolution
    # 1. Base server directory
    p1 = os.path.join(os.path.dirname(__file__), "background.png")
    if os.path.exists(p1): return FileResponse(p1)
    
    # 2. Project root (if run from outside)
    p2 = os.path.join(os.getcwd(), "server", "background.png")
    if os.path.exists(p2): return FileResponse(p2)
    
    # 3. Explicit absolute path
    p3 = "/Users/siddhant/Desktop/open_env/support_ticket_triage/server/background.png"
    if os.path.exists(p3): return FileResponse(p3)

    return {"error": "Image not found"}

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
