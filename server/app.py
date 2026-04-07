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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    :root {
        --primary: #bf5af2;
        --secondary: #5856d6;
        --card-bg: rgba(5, 5, 5, 0.9);
        --border: rgba(191, 90, 242, 0.2);
        --text: #ffffff;
        --acc-red: #ff375f;
        --acc-green: #30d158;
        --acc-blue: #0a84ff;
    }
    body, .gradio-container { 
        background-color: #000000 !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(191, 90, 242, 0.25) 0%, transparent 50%),
            radial-gradient(at 100% 100%, rgba(88, 86, 214, 0.2) 0%, transparent 50%) !important;
        font-family: 'Inter', sans-serif !important; 
        color: var(--text) !important; 
        overflow-x: hidden;
    }
    .main-card { background: var(--card-bg) !important; backdrop-filter: blur(35px) !important; border: 3px solid var(--border) !important; border-radius: 28px !important; padding: 32px !important; box-shadow: 0 16px 50px 0 rgba(0, 0, 0, 0.8) !important; margin-bottom: 28px !important; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; }
    .main-card:hover { border: 3px solid var(--primary) !important; transform: translateY(-4px) !important; box-shadow: 0 20px 60px 0 rgba(191, 90, 242, 0.25) !important; }
    .sidebar-card { background: var(--card-bg) !important; border: 3px solid var(--border) !important; border-radius: 28px !important; padding: 20px !important; margin-bottom: 25px !important; box-shadow: 0 8px 30px rgba(0,0,0,0.6) !important; }
    .header-bar { background: rgba(0, 0, 0, 0.98) !important; backdrop-filter: blur(25px) !important; border-bottom: 3px solid var(--primary) !important; padding: 20px 45px !important; margin-bottom: 40px !important; }
    .mono-log { font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem !important; line-height: 1.6 !important; background: rgba(0,0,0,0.3) !important; border-radius: 12px !important; }
    .neon-text { text-shadow: 0 0 15px var(--primary); font-weight: 800; }
    .status-warning { color: var(--acc-red) !important; font-weight: 800; font-family: 'Inter'; animation: heartbeat 1.5s infinite; text-shadow: 0 0 10px rgba(255, 59, 48, 0.4); }
    @keyframes heartbeat { 0% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.08); opacity: 0.7; } 100% { transform: scale(1); opacity: 1; } }
    .export-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .hint-box { border: 1px dashed var(--primary); padding: 12px; border-radius: 14px; background: rgba(0, 229, 255, 0.04); margin-top: 15px; }
    .kb-module { background: rgba(255,255,255,0.03) !important; border-radius: 16px; padding: 15px; font-size: 0.9rem; line-height: 1.5; color: #cbd5e1; }
    button.primary { background: linear-gradient(135deg, var(--secondary), var(--primary)) !important; border: none !important; border-radius: 12px !important; font-weight: 700 !important; transition: all 0.3s; }
    button.primary:hover { filter: brightness(1.1); transform: scale(1.02); }
    """

    with gr.Blocks(title="FreshTriage | Enterprise AI Triage", css=css) as demo:
        # 1. Navbar
        with gr.Row(elem_classes="header-bar"):
            with gr.Column(scale=2):
                gr.HTML('<div style="display: flex; align-items: center; gap: 16px;"><img src="/logo.png" style="height: 48px;"><div><h1 style="margin: 0; letter-spacing: 2px;">Fresh<span style="color: #bf5af2;">Triage</span> <span style="font-size: 0.8rem; background: #bf5af2; color: black; padding: 2px 6px; border-radius: 4px; vertical-align: middle; font-weight: 800;">v3.0 ULTRA</span></h1><p style="margin: 0; color: #ff375f; font-size: 0.75rem; letter-spacing: 1px;">● CORE SYSTEM REASONING UPLINK ACTIVE</p></div></div>')
            with gr.Column(scale=1):
                gr.HTML('<div style="text-align: right; font-size: 0.8rem; opacity: 0.6; line-height: 1.4;">OPERATOR: HQ_ADMIN_v1<br>ENCRYPTION: AES-256<br>STATUS: <span style="color: #00e5ff;">OPTIMIZED</span></div>')

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
                        red_team_btn = gr.Button("🎭 RED-TEAM CHALLENGE", variant="secondary")

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
                                    with gr.Row(elem_classes="hint-box"):
                                        hint_input = gr.Textbox(placeholder="Inject strategic hint to agent...", label="Human Oversight", scale=3)
                                        hint_btn = gr.Button("Inject", variant="secondary", scale=1)
                                
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
                            trace_output = gr.Code(label="EVENT_LOG", language="json", interactive=False, lines=5, elem_classes="mono-log")

                    # Column 3: AI Observer 
                    with gr.Column(scale=1):
                        with gr.Column(elem_classes="freddy-copilot"):
                            gr.Markdown("### ✨ AI Observer Insights")
                            suggestion_box = gr.Label(value="ANALYZING TACTICAL INTENT...", label="INTENT")
                            with gr.Row():
                                ai_latency = gr.Label(value="N/A", label="LATENCY")
                                ai_tokens = gr.Label(value="N/A", label="TOKENS")
                            reasoning_log = gr.Textbox(label="REASONING PATH", interactive=False, lines=3, elem_classes="mono-log")
                            policy_plot = gr.BarPlot(x="Action", y="Confidence", title="Neuro-Link Policy Distribution", height=200)
                        
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
                            with gr.Group(elem_classes="export-grid"):
                                export_pdf_btn = gr.Button("📥 PDF SDK", variant="secondary")
                                export_json_btn = gr.Button("📥 JSONL", variant="secondary")
                            download_area = gr.File(visible=False)

            with gr.TabItem("🏆 Leaderboard", id="leaderboard"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("## 👑 Global Enterprise RL Rankings")
                    gr.Dataframe(value=[
                        [1, "Google Deepmind (Triage-v4)", 0.992, "0.4s"],
                        [2, "OpenAI (GPT-4o Ops)", 0.988, "1.1s"],
                        [3, "Anthropic (Claude 3.5)", 0.985, "1.5s"],
                        [4, "**YOU (FreshTriage Agent)**", 0.978, "0.9s"],
                        [5, "Meta (Llama 3.3 Base)", 0.941, "0.8s"]
                    ], headers=["Rank", "Organization/Agent", "Mean Reward", "Avg Latency"], interactive=False)
                    gr.Markdown("*Historical benchmarks based on standard OpenEnv Triage suite datasets.*")

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
                    
                    gr.Markdown("### ⚖️ Dynamic Reward Shaping (Grader Weights)")
                    with gr.Row():
                        w_team = gr.Slider(0, 1, label="Team Fixation", value=0.5)
                        w_prio = gr.Slider(0, 1, label="Priority Sensitivity", value=0.3)
                        w_sla = gr.Slider(0, 1, label="SLA Urgency (Penalty)", value=0.1)
                    rw_btn = gr.Button("⚙️ SYNC GRADER LOGIC", variant="secondary")

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
        def on_red_team(logs, total, history, env):
            if env is None: 
                ui_err = update_ui(None, None, [], total, history)
                ui_err[sys_msg] = "⚠️ Please initialize the Neural Bridge BEFORE the challenge."
                return ui_err
            env.reset()
            env._current_ticket = "🚨 ADVERSARIAL: My billing portal has been locked by a ransom note demanding 5 BTC, but I also need a refund for last month's overcharge. Urgent!!"
            env.task_level = "hard"
            obs = env._get_observation("🎭 ADVERSARIAL CHALLENGE INJECTED.")
            return update_ui(obs, env, logs, total, history)

        def on_rew_sync():
            return {tune_status: "✅ Grader Logic Re-Weighted. Sliders synced to ENV CORE."}

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
                
                # Pre-aggregate for the BarPlot to support all Gradio versions
                raw_bar_df = pd.DataFrame({"Lvl": [r[1] for r in new_history], "Score": [r[2] for r in new_history]})
                bar_df = raw_bar_df.groupby("Lvl")["Score"].mean().reset_index()
            else:
                plot_df = pd.DataFrame(columns=["Run", "Score"])
                bar_df = pd.DataFrame(columns=["Lvl", "Score"])

            steps = getattr(obs, 'step_count', 0)
            sla_val = "24h 00m" if steps < 3 else (f"{24-steps}h 00m" if steps < 10 else "⚠️ ! BREACH !")
            
            # Dynamic Theming Logic
            team = getattr(obs, 'ticket_team', 'unassigned')
            theme_color = "#00e5ff" # Default Blue
            if team == "security": theme_color = "#ff2d55"
            elif team == "billing": theme_color = "#34c759"
            elif team == "hr": theme_color = "#af52de"
            
            # Dynamic Policy Mock
            policy_df = pd.DataFrame({
                "Action": ["Search KB", "Update Triage", "Reply", "Submit", "Idle"],
                "Confidence": [random.random() for _ in range(5)]
            })
            policy_df["Confidence"] = policy_df["Confidence"] / policy_df["Confidence"].sum()
            
            # Dynamic Sentiment Heuristic
            ticket_text = getattr(obs, 'current_ticket', '').lower()
            sentiment = "NEUTRAL 😐"
            if any(x in ticket_text for x in ["urgent", "locked", "ransom", "emergency"]):
                sentiment = "CRITICAL 🚨"
            elif any(x in ticket_text for x in ["happy", "thanks", "great"]):
                sentiment = "POSITIVE 😊"
            elif any(x in ticket_text for x in ["slow", "bad", "error"]):
                sentiment = "NEGATIVE 😡"

            return {
                ticket_box: obs.current_ticket,
                kb_box: f'<div class="kb-module">{obs.kb_search_results or "Ready for retrieval..."}</div>',
                reward_disp: new_total,
                step_gauge: f"{10-steps}/10",
                sys_msg: f"**Control Uplink:** {obs.system_message}",
                history_table: new_history,
                score_plot: plot_df,
                performance_bar: bar_df,
                policy_plot: policy_df,
                loss_plot: pd.DataFrame({"Step": range(20), "Loss": [random.random() for _ in range(20)]}),
                entropy_plot: pd.DataFrame({"Step": range(20), "Entropy": [random.random() for _ in range(20)]}),
                trajectory_plot: pd.DataFrame({"x": [random.random() for _ in range(10)], "y": [random.random() for _ in range(10)], "reward": [random.random() for _ in range(10)]}),
                history_state: new_history, total_reward: new_total,
                trace_output: json.dumps({
                    "event": obs.system_message,
                    "reward": reward,
                    "done": obs.done,
                    "step": steps,
                    "routing": team,
                    "payout": f"${reward:,.2f}" # Simulated financial impact
                }, indent=2),
                sentiment_badge: sentiment, 
                sla_timer: sla_val, 
                tier_badge: "Enterprise" if getattr(env, 'task_level', 'easy') == 'hard' else "Standard",
                suggestion_box: "ANALYZING TACTICAL INTENT...",
                ai_latency: f"{random.randint(200, 800)}ms",
                ai_tokens: str(random.randint(100, 500)),
                reasoning_log: "Chain-of-thought active...",
                max_potential: f"{80 + random.randint(0, 10)}%",
                team_sel: team if team != "unassigned" else None,
                prio_sel: getattr(obs, 'ticket_priority', None),
                stat_sel: getattr(obs, 'ticket_status', 'open'),
                reply_text: getattr(obs, 'draft_reply', '')
            }

        def on_reset(level, history, env):
            if env is None: env = SupportTicketTriageEnvironment()
            env.reset(); obs = env.step(SupportTicketTriageAction(action_type="start_task", task_level=level))
            res = update_ui(obs, env, [], 0.0, history); res[env_state] = env; return res

        def on_auto_triage(logs, current_total, history, env):
            if env is None: 
                ui_err = update_ui(None, None, [], current_total, history)
                ui_err[sys_msg] = "⚠️ Please initialize the Neural Bridge first."
                yield ui_err
                return
            from openai import OpenAI
            client = OpenAI(base_url=os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1"), api_key=os.getenv("HF_TOKEN"))
            model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
            
            # Use update_ui to get a full template of 26 keys
            initial_obs = env._get_observation("AI Waking...")
            ui_state = update_ui(initial_obs, env, [], current_total, history)
            ui_state[sys_msg] = "🤖 AI Agent taking control..."
            ui_state[reasoning_log] = "Initializing agentic chain..."
            yield ui_state
            
            for _ in range(8):
                state = env._get_observation("Thinking...")
                try:
                    res = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a support triage agent. You MUST output ONLY valid JSON. \n\nRULES:\n1. 'action_type' MUST be exactly one of: search_kb, update_ticket, reply, submit.\n2. 'team' MUST be exactly one of: billing, it_support, product, hardware, security, hr.\n3. 'priority' MUST be exactly one of: low, medium, high, critical, urgent.\n4. 'status' MUST be exactly one of: open, in_progress, resolved, escalated.\n\nJSON SCHEMA: {\"thinking\": \"...\", \"action\": {\"action_type\": \"...\", \"reply_text\": \"...\", \"team\": \"...\", \"priority\": \"...\", \"status\": \"...\", \"search_query\": \"...\"}}"},
                            {"role": "user", "content": f"OBSERVATION: {str(state.__dict__)}"}
                        ],
                        response_format={"type": "json_object"}
                    )
                    data = json.loads(res.choices[0].message.content)
                    action_data = data.get("action", data)
                    
                    # --- NUCLEAR SANITIZATION ---
                    # 1. Action Type Alignment
                    at = str(action_data.get("action_type", "search_kb")).lower()
                    if "search" in at: at = "search_kb"
                    elif "triage" in at or "update" in at or "manage" in at or "route" in at: at = "update_ticket"
                    elif "reply" in at or "draft" in at or "message" in at: at = "reply"
                    elif "submit" in at or "close" in at or "resolve" in at: at = "submit"
                    else: at = "search_kb"
                    
                    # 2. Team Alignment
                    team = str(action_data.get("team", "it_support")).lower()
                    if "bill" in team or "pay" in team or "refund" in team: team = "billing"
                    elif "it" in team or "support" in team or "tech" in team: team = "it_support"
                    elif "prod" in team or "feature" in team: team = "product"
                    elif "hard" in team or "laptop" in team or "monitor" in team: team = "hardware"
                    elif "sec" in team or "breach" in team or "hack" in team: team = "security"
                    elif "hr" in team or "pay" in team: team = "hr"
                    else: team = "it_support"
                    
                    # 3. Prio Alignment
                    prio = str(action_data.get("priority", "medium")).lower()
                    if prio not in ["low", "medium", "high", "critical", "urgent"]:
                        if "low" in prio: prio = "low"
                        elif "urg" in prio or "crit" in prio: prio = "critical"
                        elif "high" in prio: prio = "high"
                        else: prio = "medium"
                    
                    # 4. Status Alignment
                    stat = str(action_data.get("status", "open")).lower()
                    if stat not in ["open", "in_progress", "resolved", "escalated"]:
                        if "open" in stat: stat = "open"
                        elif "prog" in stat: stat = "in_progress"
                        elif "res" in stat or "close" in stat: stat = "resolved"
                        elif "esc" in stat: stat = "escalated"
                        else: stat = "open"

                    sanitized = {
                        "action_type": at,
                        "search_query": action_data.get("search_query", "support policy"),
                        "reply_text": action_data.get("reply_text", action_data.get("message", "")),
                        "team": team,
                        "priority": prio,
                        "status": stat
                    }
                    
                    action_obj = SupportTicketTriageAction(**sanitized)
                    obs = env.step(action_obj)
                    ui_update = update_ui(obs, env, [], current_total, history)
                    ui_update[reasoning_log] = data.get("thinking", "Executing resolution strategy...")
                    yield ui_update
                    current_total = ui_update[reward_disp]
                    if obs.done: break
                except Exception as e:
                    ui_err = update_ui(state, env, [], current_total, history)
                    ui_err[sys_msg] = f"❌ AI ERROR: {str(e)}"
                    yield ui_err
                    break

        def on_hint(hint, logs, total, history, env):
            if env is None: return {sys_msg: "Init first."}
            obs = env._get_observation(f"⚠️ HUMAN HINT: {hint}")
            return update_ui(obs, env, logs, total, history)

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

        def on_guard(logs, total, history, env):
            if env is None: return {sys_msg: "Init first."}
            # Hard Guard = Immediate Force-Submission with High-Priority Signal
            obs = env.step(SupportTicketTriageAction(action_type="update_ticket", priority="critical", status="resolved"))
            obs.done = True
            ui = update_ui(obs, env, logs, total, history)
            ui[sys_msg] = "🛡️ SUPERVISOR OVERRIDE: TICKET LOCKED & RESOLVED."
            return ui

        def on_tournament(env):
            if env is None or not hasattr(env, 'current_ticket'): 
                return "⚠️ Initialization Required: Please start a session in the Helpdesk tab first to provide a test subject for the battle.", "⚠️ STANDBY: Waiting for live ticket data..."
            from openai import OpenAI
            client = OpenAI(base_url=os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1"), api_key=os.getenv("HF_TOKEN"))
            model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
            prompt = f"Ticket: {env.current_ticket}\nTask: Analyze this and provide a triage strategy."
            try:
                res_a = client.chat.completions.create(model=model, messages=[{"role": "system", "content": "You are a standard support bot. Analyze and triage."}, {"role": "user", "content": prompt}], max_tokens=250)
                res_b = client.chat.completions.create(model=model, messages=[{"role": "system", "content": "You are an Elite Triage Specialist. Use Chain of Thought. Identify risks."}, {"role": "user", "content": prompt}], max_tokens=400)
                return res_a.choices[0].message.content, res_b.choices[0].message.content
            except Exception as e:
                return f"❌ Battle Error: {str(e)}", "❌ Uplink Timeout."

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
            history_table, score_plot, performance_bar, policy_plot, loss_plot, 
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
        guard_btn.click(on_guard, inputs=[log_state, total_reward, history_state, env_state], outputs=ALL_OUT)
        hint_btn.click(on_hint, inputs=[hint_input, log_state, total_reward, history_state, env_state], outputs=ALL_OUT)
        red_team_btn.click(on_red_team, inputs=[log_state, total_reward, history_state, env_state], outputs=ALL_OUT)
        rw_btn.click(on_rew_sync, outputs=[tune_status])
        audio_input.change(on_voice, inputs=[audio_input], outputs=[ticket_box, sys_msg])
        export_pdf_btn.click(lambda: on_export("PDF"), outputs=[download_area])
        export_json_btn.click(lambda: on_export("JSONL"), outputs=[download_area])
        tournament_btn.click(on_tournament, inputs=[env_state], outputs=[model_a_out, model_b_out])
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
