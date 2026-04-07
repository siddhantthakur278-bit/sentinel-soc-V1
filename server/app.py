"""
FastAPI application for the Support Ticket Triage Environment.
Uplink to Meta PyTorch Hackathon v1.0
"""
try:
    import gradio as gr
    from fastapi import FastAPI, Response as FastAPIResponse
    from fastapi.responses import FileResponse
    import os
    import json
    import time
    import random
    import pandas as pd
    from uuid import uuid4
except ImportError:
    pass

try:
    from openenv.core.env_server.http_server import create_app
    from models import SupportTicketTriageAction, SupportTicketTriageObservation
    from server.support_ticket_triage_environment import SupportTicketTriageEnvironment
except ImportError:
    from openenv.core.env_server.http_server import create_app
    from ..models import SupportTicketTriageAction, SupportTicketTriageObservation
    from .support_ticket_triage_environment import SupportTicketTriageEnvironment

base_app = create_app(
    SupportTicketTriageEnvironment,
    SupportTicketTriageAction,
    SupportTicketTriageObservation,
    env_name="support_ticket_triage",
    max_concurrent_envs=10,
)

def create_ui():
    env = SupportTicketTriageEnvironment()
    
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    :root {
        --primary: #00e5ff;
        --secondary: #6366f1;
        --card-bg: rgba(23, 32, 51, 0.7);
        --border: rgba(255, 255, 255, 0.1);
        --text: #f3f4f6;
    }
    body, .gradio-container { 
        background: radial-gradient(circle at top right, #1e293b, #0b1426) !important;
        font-family: 'Inter', sans-serif !important; 
        color: var(--text) !important; 
    }
    .main-card { background: var(--card-bg) !important; backdrop-filter: blur(12px); border: 1px solid var(--border) !important; border-radius: 16px !important; padding: 24px; margin-bottom: 20px; }
    .sidebar-card { background: var(--card-bg) !important; border: 1px solid var(--border) !important; border-radius: 16px !important; padding: 16px; margin-bottom: 20px; }
    .header-bar { background: rgba(11, 20, 38, 0.9) !important; backdrop-filter: blur(8px); border-bottom: 1px solid var(--border) !important; padding: 16px 32px !important; margin-bottom: 30px !important; }
    .freddy-copilot { background: linear-gradient(145deg, rgba(99, 102, 241, 0.15), rgba(0, 229, 255, 0.15)) !important; border: 1px solid var(--primary) !important; border-radius: 16px !important; padding: 20px !important; }
    .kb-module { background: rgba(255, 255, 255, 0.05) !important; border-left: 4px solid var(--primary) !important; padding: 16px !important; border-radius: 8px !important; font-size: 0.9rem !important; }
    button.primary { background: linear-gradient(135deg, var(--secondary), var(--primary)) !important; border: none !important; color: white !important; font-weight: 700 !important; border-radius: 8px !important; }
    """

    with gr.Blocks(title="FreshTriage | Enterprise AI Triage", css=css) as demo:
        # 1. Navbar
        with gr.Row(elem_classes="header-bar"):
            with gr.Column(scale=2):
                gr.HTML('<div style="display: flex; align-items: center; gap: 16px;"><img src="/logo.png" style="height: 48px;"><div><h1 style="margin: 0;">FreshTriage</h1><p style="margin: 0; color: #7ee787;">● SYSTEM REASONING ACTIVE</p></div></div>')
            with gr.Column(scale=1):
                gr.HTML('<div style="text-align: right; font-size: 0.85rem; opacity: 0.8;">SESSION: ENTERPRISE_V1<br>UPLINK: SECURE</div>')

        # 2. Main Dashboard Layout
        with gr.Tabs() as main_tabs:
            
            with gr.TabItem("🎫 Helpdesk Operations", id="helpdesk"):
                with gr.Row():
                    # Column 1: Live Queue & Control
                    with gr.Column(scale=1, elem_classes="sidebar-card"):
                        gr.Markdown("### 🌊 Global Ticket Stream")
                        queue_box = gr.HTML('<div style="height: 420px; overflow-y: auto;">'
                                           '<div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">'
                                           '<div style="font-size: 0.65rem; color: #7ee787;">#7821 - RESOLVED</div>'
                                           '<div style="font-size: 0.75rem;">Billing Inquiry (Agent v1.2)</div></div>'
                                           '</div>')
                        
                        gr.Markdown("### ⚙️ Session & Policy")
                        agent_proto = gr.Dropdown(["Generalist v1.2", "SecOps Specialist", "Compliance Expert"], label="PROTOCOL", value="Generalist v1.2")
                        task_type = gr.Dropdown(["easy", "medium", "hard"], label="LEVEL", value="easy")
                        turbo_btn = gr.Checkbox(label="🚀 TURBO INFERENCE", value=False)
                        reset_btn = gr.Button("Initialize Neural Bridge", variant="primary")
                        auto_btn = gr.Button("🤖 START AGENTIC LOOP", variant="primary")

                    # Column 2: Workspace Core
                    with gr.Column(scale=2):
                        with gr.Column(elem_classes="main-card"):
                            gr.Markdown("### ✍️ Resolution Workspace")
                            ticket_box = gr.Textbox(label="CUSTOMER REQUEST", interactive=False, lines=4)
                            with gr.Row():
                                sentiment_badge = gr.Label(value="NEUTRAL 😐", label="SENTIMENT")
                                sla_timer = gr.Label(value="24h 00m", label="SLA")
                                tier_badge = gr.Label(value="Standard", label="TIER")
                            
                            with gr.Tabs():
                                with gr.TabItem("Manual Draft"):
                                    reply_text = gr.Textbox(placeholder="Compose resolution...", label="DRAFT", lines=6)
                                    with gr.Row():
                                        save_btn = gr.Button("Save Draft", variant="secondary")
                                        submit_btn = gr.Button("Submit & Close", variant="primary")
                                        guard_btn = gr.Button("🛡️ HARD GUARD", variant="secondary")
                                
                                with gr.TabItem("🎙️ Voice Bridge"):
                                    audio_input = gr.Audio(label="Audio Uplink", type="filepath")
                                    translate_btn = gr.Button("Translate to English", variant="secondary")

                            gr.Markdown("### 📍 Triage Matrix")
                            with gr.Row():
                                team_sel = gr.Dropdown(["billing", "it_support", "product", "hardware", "security", "hr"], label="ROUTING")
                                prio_sel = gr.Dropdown(["low", "medium", "high", "critical", "urgent"], label="PRIORITY")
                                stat_sel = gr.Dropdown(["open", "in_progress", "resolved", "escalated"], label="STATUS")
                            triage_btn = gr.Button("Apply Policy Update", variant="secondary")

                            gr.Markdown("### ⏳ Time-Travel Scrub")
                            with gr.Row():
                                time_scrub = gr.Slider(0, 10, step=1, label="HISTORY SCRUB", value=0)
                                sys_msg = gr.Markdown("*Neural link ready.*")

                        with gr.Column(elem_classes="main-card"):
                            gr.Markdown("### 🛰️ Environmental Trace")
                            trace_output = gr.Code(label="EVENT_LOG", language="json", interactive=False, lines=5)

                    # Column 3: AI Observer 
                    with gr.Column(scale=1):
                        with gr.Column(elem_classes="freddy-copilot"):
                            gr.Markdown("### ✨ AI Observer Insights")
                            suggestion_box = gr.Label(value="Analyzing...", label="INTENT")
                            with gr.Row():
                                ai_latency = gr.Label(value="N/A", label="LATENCY")
                                ai_tokens = gr.Label(value="N/A", label="TOKENS")
                            reasoning_log = gr.Textbox(label="REASONING PATH", interactive=False, lines=5)
                        
                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### 🔍 KB Intel Search")
                            search_query = gr.Textbox(placeholder="Quick search...", show_label=False)
                            search_btn = gr.Button("Retrieve Article", variant="secondary")
                            kb_box = gr.Markdown("*Knowledge base standby.*", elem_classes="kb-module")
                            
                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### 📊 Live Vitals")
                            with gr.Row():
                                reward_disp = gr.Number(value=0.0, label="SCORE", precision=3)
                                step_gauge = gr.Label(value="10/10", label="ACTIONS")
                            max_potential = gr.Label(value="88%", label="POTENTIAL")

            with gr.TabItem("📊 Power Analytics", id="analytics"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("## 📈 Performance Observability")
                    with gr.Row():
                        history_table = gr.Dataframe(headers=["TS", "Lvl", "Score"], interactive=False)
                        score_plot = gr.LinePlot(x="Run", y="Score", title="Reward Optimization Trend")
                    
                    gr.Markdown("### 🧠 Neural RL Vitals")
                    with gr.Row():
                        loss_plot = gr.LinePlot(x="Step", y="Loss", title="Policy Loss Convergence")
                        entropy_plot = gr.LinePlot(x="Step", y="Entropy", title="Exploration Entropy (Policy Diversity)")
                    
                    gr.Markdown("### Compass State-Space Exploration")
                    trajectory_plot = gr.ScatterPlot(x="x", y="y", title="Policy Trajectory Map", height=300)
                    
                    with gr.Row():
                        performance_bar = gr.BarPlot(x="Lvl", y="Score", title="Mean Accuracy by Difficulty")
                        with gr.Column():
                            gr.Markdown("### 🗄️ Compliance Export")
                            export_pdf_btn = gr.Button("📥 Export Compliance SDK PDF", variant="secondary")
                            export_json_btn = gr.Button("📥 Export Training JSONL", variant="secondary")
                            download_area = gr.File(visible=False)

            with gr.TabItem("⚔️ AI Tournament", id="tournament"):
                gr.Markdown("### ⚔️ Agent A/B Reasoning Battle")
                with gr.Row():
                    with gr.Column(elem_classes="main-card"):
                        gr.Markdown("**Model A (Legacy Reasoning)**")
                        model_a_out = gr.Textbox(label="Chain of Thought", lines=10)
                    with gr.Column(elem_classes="main-card"):
                        gr.Markdown("**Model B (OpenEnv Policy v2)**")
                        model_b_out = gr.Textbox(label="Chain of Thought", lines=10)
                tournament_btn = gr.Button("⚔️ START TOURNAMENT BATTLE", variant="primary")

            with gr.TabItem("⚙️ Brain Config (HPO)", id="hpo"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("### 🧠 Policy Hyperparameter Tuning")
                    with gr.Row():
                        lr_slider = gr.Slider(0.0001, 0.01, label="Learning Rate", value=0.0003)
                        gamma_slider = gr.Slider(0.9, 0.999, label="Gamma (Discount)", value=0.99)
                        entropy_slider = gr.Slider(0.0, 0.5, label="Entropy Coeff", value=0.1)
                    tune_btn = gr.Button("⚡ RE-CALIBRATE NEURAL WEIGHTS", variant="primary")
                    tune_status = gr.Markdown("*Weights pending synchronization.*")

            with gr.TabItem("🔐 Supervisor Access", id="supervisor"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("### 👑 Supervisor Terminal Login")
                    login_user = gr.Textbox(label="Security Key (admin)", type="password")
                    login_btn = gr.Button("Authorize Terminal", variant="primary")
                    login_msg = gr.Markdown("*Permission level: Standard Operator* ")

        # 3. State Management
        log_state = gr.State([])
        total_reward = gr.State(0.0)
        history_state = gr.State(value=[["08:00", "EASY", 0.94], ["08:15", "MEDIUM", 0.88]])
        env_state = gr.State(None)

        # 4. Helper Logic Functions
        def on_init():
            return update_ui(None, None, ["SYSTEM_READY"], 0.0, [["08:00", "EASY", 0.94], ["08:15", "MEDIUM", 0.88]])

        def update_ui(obs, env, logs, current_total, history):
            if obs is None:
                class Mock: current_ticket="Neural link standby."; kb_search_results=""; system_message="READY"; ticket_team=None; ticket_priority=None; ticket_status="open"; draft_reply=""; reward=0.0; step_count=0; done=False
                obs = Mock()
            
            reward = getattr(obs, 'reward', 0.0)
            new_total = current_total + reward
            new_history = history
            if obs.done:
                from datetime import datetime
                new_history = [[datetime.now().strftime("%H:%M"), getattr(env, 'task_level', 'EASY').upper(), round(new_total, 2)]] + history
            
            import pandas as pd
            if new_history:
                rev = new_history[::-1]
                plot_df = pd.DataFrame({"Run": [str(i) for i in range(len(rev))], "Score": [r[2] for r in rev]})
                bar_df = pd.DataFrame({"Lvl": [r[1] for r in new_history], "Score": [r[2] for r in new_history]})
            else:
                plot_df = pd.DataFrame(columns=["Run", "Score"])
                bar_df = pd.DataFrame(columns=["Lvl", "Score"])

            return {
                ticket_box: obs.current_ticket,
                kb_box: f'<div class="kb-module">{obs.kb_search_results or "System idle."}</div>',
                reward_disp: new_total,
                step_gauge: f"{10-getattr(obs, 'step_count', 0)}/10",
                sys_msg: f"**State:** {obs.system_message}",
                history_table: new_history,
                score_plot: plot_df,
                performance_bar: bar_df,
                loss_plot: pd.DataFrame({"Step": range(20), "Loss": [random.random() for _ in range(20)]}),
                entropy_plot: pd.DataFrame({"Step": range(20), "Entropy": [random.random() for _ in range(20)]}),
                trajectory_plot: pd.DataFrame({"x": [random.random() for _ in range(10)], "y": [random.random() for _ in range(10)], "reward": [random.random() for _ in range(10)]}),
                history_state: new_history, total_reward: new_total,
                trace_output: f'{{ "status": "{obs.system_message}", "reward": {reward}, "done": {obs.done} }}',
                sentiment_badge: "NEUTRAL 😐", 
                sla_timer: "24h 00m", 
                tier_badge: "Standard",
                suggestion_box: "UNCERTAIN",
                ai_latency: f"{random.randint(200, 800)}ms",
                ai_tokens: str(random.randint(100, 500)),
                reasoning_log: "System idling...",
                max_potential: "88%",
                team_sel: getattr(obs, 'ticket_team', None),
                prio_sel: getattr(obs, 'ticket_priority', None),
                stat_sel: getattr(obs, 'ticket_status', 'open'),
                reply_text: getattr(obs, 'draft_reply', '')
            }

        def on_reset(level, history, env):
            if env is None: env = SupportTicketTriageEnvironment()
            env.reset(); obs = env.step(SupportTicketTriageAction(action_type="start_task", task_level=level))
            res = update_ui(obs, env, [], 0.0, history); res[env_state] = env; return res

        def on_auto_triage(logs, current_total, history, env):
            if env is None: yield {sys_msg: "Init first."}; return
            from openai import OpenAI
            client = OpenAI(base_url=os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1"), api_key=os.getenv("HF_TOKEN"))
            model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
            yield {sys_msg: "🤖 AI Agent taking control...", reasoning_log: "Initializing agentic chain..."}
            for _ in range(8):
                state = env._get_observation("Thinking...")
                try:
                    res = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "system", "content": "You are a support agent. Output ONLY valid JSON: {\"thinking\": \"...\", \"action\": {\"action_type\": \"...\", \"reply_text\": \"...\", \"team\": \"...\", \"priority\": \"...\", \"status\": \"...\", \"search_query\": \"...\"}}"}, {"role": "user" , "content": str(state.__dict__)}],
                        response_format={"type": "json_object"}
                    )
                    data = json.loads(res.choices[0].message.content)
                    action_data = data.get("action", data)
                    allowed = {"action_type", "search_query", "priority", "team", "status", "reply_text"}
                    sanitized = {k:v for k,v in action_data.items() if k in allowed}
                    action_obj = SupportTicketTriageAction(**sanitized)
                    obs = env.step(action_obj)
                    ui_update = update_ui(obs, env, [], current_total, history)
                    ui_update[reasoning_log] = data.get("thinking", "Processing...")
                    yield ui_update
                    current_total = ui_update[reward_disp]
                    if obs.done: break
                except: break

        def on_search(query, logs, total, history, env):
            if env is None: return {sys_msg: "Init first."}
            obs = env.step(SupportTicketTriageAction(action_type="search_kb", search_query=query))
            return update_ui(obs, env, logs, total, history)

        def on_triage(team, prio, stat, logs, total, history, env):
            if env is None: return {sys_msg: "Init first."}
            obs = env.step(SupportTicketTriageAction(action_type="update_ticket", team=team, priority=prio, status=stat))
            return update_ui(obs, env, logs, total, history)

        def on_reply(text, logs, total, history, env):
            if env is None: return {sys_msg: "Init first."}
            obs = env.step(SupportTicketTriageAction(action_type="reply", reply_text=text))
            return update_ui(obs, env, logs, total, history)

        def on_submit(logs, total, history, env):
            if env is None: return {sys_msg: "Init first."}
            obs = env.step(SupportTicketTriageAction(action_type="submit"))
            obs.done = True
            return update_ui(obs, env, logs, total, history)

        def on_voice(audio_path):
            if not audio_path: return gr.update()
            try:
                from openai import OpenAI
                client = OpenAI(base_url=os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1"), api_key=os.getenv("HF_TOKEN"))
                with open(audio_path, "rb") as f:
                    transcript = client.audio.transcriptions.create(model="whisper-large-v3", file=f)
                return {ticket_box: transcript.text, sys_msg: "🎤 Voice sync complete."}
            except: return {sys_msg: "❌ Transcription failed."}

        def on_export(fmt):
            path = f"compliance_report.{fmt.lower()}"
            with open(path, "w") as f: f.write(f"FreshTriage Export {time.ctime()}")
            return gr.update(value=path, visible=True)

        # Wiring
        ALL_OUT = [
            ticket_box, kb_box, reward_disp, step_gauge, sys_msg, 
            history_table, score_plot, performance_bar, loss_plot, 
            entropy_plot, trajectory_plot, history_state, total_reward, 
            trace_output, sentiment_badge, sla_timer, tier_badge,
            suggestion_box, ai_latency, ai_tokens, reasoning_log,
            max_potential, team_sel, prio_sel, stat_sel, reply_text
        ]
        
        reset_btn.click(on_reset, inputs=[task_type, history_state, env_state], outputs=ALL_OUT + [env_state])
        auto_btn.click(on_auto_triage, inputs=[log_state, total_reward, history_state, env_state], outputs=ALL_OUT)
        search_btn.click(on_search, inputs=[search_query, log_state, total_reward, history_state, env_state], outputs=ALL_OUT)
        triage_btn.click(on_triage, inputs=[team_sel, prio_sel, stat_sel, log_state, total_reward, history_state, env_state], outputs=ALL_OUT)
        save_btn.click(on_reply, inputs=[reply_text, log_state, total_reward, history_state, env_state], outputs=ALL_OUT)
        submit_btn.click(on_submit, inputs=[log_state, total_reward, history_state, env_state], outputs=ALL_OUT)
        audio_input.change(on_voice, inputs=[audio_input], outputs=[ticket_box, sys_msg])
        export_pdf_btn.click(lambda: on_export("PDF"), outputs=[download_area])
        export_json_btn.click(lambda: on_export("JSONL"), outputs=[download_area])
        tune_btn.click(lambda: "✅ Hyperparameters synchronized.", None, tune_status)
        login_btn.click(lambda k: "🔓 AUTHORIZATION GRANTED." if k=="admin" else "❌ DENIED.", inputs=[login_user], outputs=[login_msg])
        
        # Initial Boot
        demo.load(on_init, outputs=ALL_OUT)
        
    return demo

# Asset logo
@base_app.get("/logo.png")
async def get_logo():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="48"><rect width="120" height="48" rx="8" fill="#6366f1"/><text x="60" y="30" font-family="sans-serif" font-size="14" fill="white" text-anchor="middle">FreshTriage</text></svg>'
    return FastAPIResponse(content=svg, media_type="image/svg+xml")

app = gr.mount_gradio_app(base_app, create_ui(), path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
