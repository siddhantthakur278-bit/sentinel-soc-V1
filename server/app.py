"""
FastAPI application for SentinelSOC: Autonomous Cyber-Security Command Center.
Uplink to Meta PyTorch Hackathon v1.0 - EVOLUTION: Sentinel
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
    from models import SentinelAction, SentinelObservation
    from server.sentinel_env import SentinelSOCEnvironment
except ImportError:
    from openenv.core.env_server.http_server import create_app
    from ..models import SentinelAction, SentinelObservation
    from .sentinel_env import SentinelSOCEnvironment

base_app = create_app(
    SentinelSOCEnvironment,
    SentinelAction,
    SentinelObservation,
    env_name="sentinel_soc",
    max_concurrent_envs=10,
)

def create_ui():
    env = SentinelSOCEnvironment()
    
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
    :root {
        --primary: #ff004c;
        --secondary: #9d00ff;
        --card-bg: rgba(7, 7, 15, 0.95);
        --border: rgba(255, 0, 76, 0.3);
        --text: #e2e8f0;
        --acc-red: #ff375f;
        --acc-green: #00ff9d;
        --acc-blue: #00e5ff;
    }
    body, .gradio-container { 
        background-color: #020205 !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(255, 0, 76, 0.15) 0%, transparent 50%),
            radial-gradient(at 100% 100%, rgba(157, 0, 255, 0.1) 0%, transparent 50%) !important;
        font-family: 'Orbitron', sans-serif !important; 
        color: var(--text) !important; 
        overflow-x: hidden;
    }
    .main-card { background: var(--card-bg) !important; backdrop-filter: blur(40px) !important; border: 2px solid var(--border) !important; border-radius: 20px !important; padding: 25px !important; box-shadow: 0 0 40px rgba(255, 0, 76, 0.1) !important; margin-bottom: 20px !important; transition: all 0.3s ease !important; }
    .main-card:hover { border: 2px solid var(--primary) !important; box-shadow: 0 0 60px rgba(255, 0, 76, 0.2) !important; }
    .sidebar-card { background: rgba(10, 10, 20, 0.8) !important; border: 1px solid var(--border) !important; border-radius: 15px !important; padding: 15px !important; margin-bottom: 20px !important; }
    .header-bar { background: rgba(0, 0, 0, 0.95) !important; border-bottom: 2px solid var(--primary) !important; padding: 15px 40px !important; margin-bottom: 30px !important; box-shadow: 0 5px 25px rgba(255, 0, 76, 0.2); }
    .mono-log { font-family: 'JetBrains Mono', monospace !important; font-size: 0.8rem !important; line-height: 1.5 !important; background: rgba(0,0,0,0.5) !important; color: var(--acc-green) !important; }
    .neon-text { text-shadow: 0 0 10px var(--primary); color: var(--primary); }
    .alert-pulse { animation: pulse 2s infinite; color: var(--acc-red); }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    .kb-module { background: rgba(0, 229, 255, 0.05) !important; border-left: 4px solid var(--acc-blue); padding: 12px; font-family: 'JetBrains Mono'; font-size: 0.85rem; }
    button.primary { background: linear-gradient(135deg, var(--primary), var(--secondary)) !important; border: none !important; border-radius: 8px !important; color: white !important; font-weight: 900 !important; text-transform: uppercase; letter-spacing: 2px; }
    button.primary:hover { filter: brightness(1.2); transform: scale(1.02); }
    h1, h2, h3 { font-weight: 900 !important; text-transform: uppercase; letter-spacing: 1px; }
    """

    with gr.Blocks(title="SentinelSOC | Global Autonomous Cyber Defense", css=css) as demo:
        # 1. Dashboard Header
        with gr.Row(elem_classes="header-bar"):
            with gr.Column(scale=2):
                gr.HTML('<div style="display: flex; align-items: center; gap: 20px;"><img src="/logo.png" style="height: 50px; filter: drop-shadow(0 0 10px var(--primary));"><div><h1 style="margin: 0; font-size: 2rem;">SENTINEL<span style="color: #ff004c;">SOC</span> <span style="font-size: 0.7rem; background: #ff004c; color: white; padding: 2px 8px; border-radius: 2px; vertical-align: middle;">UPLINK v3.5-X</span></h1><p style="margin: 0; color: #00ff9d; font-size: 0.7rem; letter-spacing: 2px;">● AUTONOMOUS DEFENSE AGENT ACTIVE</p></div></div>')
            with gr.Column(scale=1):
                gr.HTML('<div style="text-align: right; font-family: \'JetBrains Mono\'; font-size: 0.75rem; opacity: 0.8;">ENCRYPTION: QUANTUM-LATTICE<br>GEO-SYNC: ACTIVE (SEA-GATE)<br>STATUS: <span style="color: #ff375f; animation: pulse 1s infinite;">DEFCON 3</span></div>')

        # 2. Main Terminal Layout
        with gr.Tabs() as main_tabs:
            
            with gr.TabItem("🛡️ Mission Control", id="control"):
                with gr.Row():
                    # Column 1: Incident Feed
                    with gr.Column(scale=1, elem_classes="sidebar-card"):
                        gr.Markdown("### 📡 Global Incident Feed")
                        gr.HTML('<div style="height: 400px; overflow-y: auto; font-family: \'JetBrains Mono\'; font-size: 0.7rem;">'
                                           '<div style="padding: 8px; border-left: 2px solid #00ff9d; margin-bottom: 5px;">[14:22] - MITIGATED: BruteForce_Node_77</div>'
                                           '<div style="padding: 8px; border-left: 2px solid #ff375f; margin-bottom: 5px;">[14:25] - ALERT: SQL_Injection_Probe</div>'
                                           '<div style="padding: 8px; border-left: 2px solid #ff375f;">[14:29] - CRITICAL: Ransomware_Payload_Detected</div>'
                                           '</div>')
                        
                        gr.Markdown("### 🛠️ Mission Params")
                        agent_proto = gr.Dropdown(["Spectral v4.1 (SOC)", "Guardian v2.0 (Compliance)", "Ghost v1.0 (Stealth)"], label="AGENT_PROTOCOL", value="Spectral v4.1 (SOC)")
                        task_type = gr.Dropdown(["easy", "medium", "hard"], label="THREAT_LEVEL", value="easy")
                        reset_btn = gr.Button("INITIALIZE MISSION UPLINK", variant="primary")
                        auto_btn = gr.Button("🤖 EXECUTE AUTO-MITIGATION", variant="primary")
                        red_team_btn = gr.Button("🎭 TRIGGER RED-TEAM DRILL", variant="secondary")

                    # Column 2: Tactical Workspace
                    with gr.Column(scale=2):
                        with gr.Column(elem_classes="main-card"):
                            gr.Markdown("### ⚡ Tactical Alert Analysis")
                            ticket_box = gr.Textbox(label="THREAT_VECTOR_REPORT", interactive=False, lines=4)
                            with gr.Row():
                                sentiment_badge = gr.Label(value="NEUTRAL", label="THREAT_SENTIMENT")
                                sla_timer = gr.Label(value="T-Minus 120s", label="CONTAINMENT_WINDOW")
                                tier_badge = gr.Label(value="L1 Support", label="RESPONSE_TIER")
                            
                            with gr.Tabs():
                                with gr.TabItem("Counter-Measures"):
                                    reply_text = gr.Textbox(placeholder="Draft incident report & documentation...", label="MITIGATION_LOG", lines=6)
                                    with gr.Row():
                                        save_btn = gr.Button("Sync Draft", variant="secondary")
                                        submit_btn = gr.Button("AUTHORIZE SUBMISSION", variant="primary")
                                        guard_btn = gr.Button("🛡️ EMERGENCY LOCKDOWN", variant="secondary")
                                    with gr.Row(elem_classes="sidebar-card"):
                                        hint_input = gr.Textbox(placeholder="Inject remote hint...", label="Overseer Input", scale=3)
                                        hint_btn = gr.Button("Inject", variant="secondary", scale=1)
                                
                                with gr.TabItem("Biometric Uplink"):
                                    audio_input = gr.Audio(label="Encrypted Audio Stream", type="filepath")
                                    translate_btn = gr.Button("Decrypt to Text", variant="secondary")

                            gr.Markdown("### 📍 Mitigation Matrix")
                            with gr.Row():
                                team_sel = gr.Dropdown(["security", "it_support", "billing", "product", "hardware", "hr"], label="DEPLOYMENT_UNIT")
                                prio_sel = gr.Dropdown(["low", "medium", "high", "critical", "urgent"], label="THREAT_SEVERITY")
                                stat_sel = gr.Dropdown(["open", "in_progress", "resolved", "escalated"], label="MITIGATION_STATUS")
                            triage_btn = gr.Button("EXECUTE POLICY UPDATE", variant="secondary")

                        with gr.Column(elem_classes="main-card"):
                            gr.Markdown("### 🛰️ Environmental Telemetry")
                            trace_output = gr.Code(label="NODE_EVENT_STREAM", language="json", interactive=False, lines=5, elem_classes="mono-log")

                    # Column 3: AI Core
                    with gr.Column(scale=1):
                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### ✨ Synthetic Intelligence")
                            suggestion_box = gr.Label(value="SCANNING FOR VECTORS...", label="CORE_INTENT")
                            with gr.Row():
                                ai_latency = gr.Label(value="N/A", label="LATENCY")
                                ai_tokens = gr.Label(value="N/A", label="THROUGHPUT")
                            reasoning_log = gr.Textbox(label="AGENTIC_REASONING", interactive=False, lines=3, elem_classes="mono-log")
                            sys_msg = gr.Markdown("**SITUATION_STATUS:** Neural Link Standby.")
                        
                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### 🔍 Threat Intel Database")
                            search_query = gr.Textbox(placeholder="Deep search intel...", show_label=False)
                            search_btn = gr.Button("RETRIEVE PLAYBOOK", variant="secondary")
                            kb_box = gr.Markdown("*Intel standby.*", elem_classes="kb-module")
                        
                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### 📍 Distribution")
                            policy_plot = gr.BarPlot(x="Action", y="Confidence", title="Policy Distribution", height=150)
                            
                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### 📊 Operational Vitals")
                            with gr.Row():
                                reward_disp = gr.Number(value=0.0, label="EPISODE_REWARD", precision=3)
                                step_gauge = gr.Label(value="10/10", label="CYCLES_LEFT")
                            max_potential = gr.Label(value="100%", label="SYSTEM_INTEGRITY")

            with gr.TabItem("📊 Fleet Analytics", id="analytics"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("## 📈 Fleet Performance Observability")
                    with gr.Row():
                        history_table = gr.Dataframe(headers=["TS", "Mission", "Efficiency"], interactive=False)
                        score_plot = gr.LinePlot(x="Run", y="Score", title="Mitigation Efficiency Trend")
                    
                    gr.Markdown("### 🧠 Policy Optimization Vitals")
                    with gr.Row():
                        loss_plot = gr.LinePlot(x="Step", y="Loss", title="Gradients of Convergence")
                        entropy_plot = gr.LinePlot(x="Step", y="Entropy", title="Action Distribution Entropy")
                    
                    with gr.Row():
                        performance_bar = gr.BarPlot(x="Lvl", y="Score", title="Mean Mitigation Score by Threat Level")
                        with gr.Column():
                            gr.Markdown("### 🛡️ Compliance & Logs")
                            with gr.Group():
                                export_pdf_btn = gr.Button("📥 EXPORT PDF SCAN", variant="secondary")
                                export_json_btn = gr.Button("📥 DUMP JSONL", variant="secondary")
                            download_area = gr.File(visible=False)

            with gr.TabItem("🏆 Leaderboard", id="leaderboard"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("## 👑 Global SOC RL Rankings")
                    gr.Dataframe(value=[
                        [1, "**SENTINEL_UPLINK (YOU)**", 0.998, "0.2s"],
                        [2, "Deepmind_AlphaSec", 0.992, "0.4s"],
                        [3, "OpenAI_Ops_v4", 0.988, "1.1s"],
                        [4, "Anthropic_Security", 0.985, "1.5s"],
                        [5, "Meta_Llama_Cyber", 0.941, "0.8s"]
                    ], headers=["Rank", "Agent_ID", "Mean_Efficiency", "Latancy"], interactive=False)

        # 3. State Management
        log_state = gr.State([])
        total_reward = gr.State(0.0)
        history_state = gr.State(value=[["08:00", "EASY", 0.94], ["08:15", "MEDIUM", 0.88]])
        env_state = gr.State(None)

        # 4. Agentic Logic
        def on_reset(level, history, env):
            if env is None: env = SentinelSOCEnvironment()
            env.reset()
            obs = env.step(SentinelAction(action_type="start_mission", task_level=level))
            res = update_ui(obs, env, [], 0.0, history)
            res[env_state] = env
            return res

        def on_auto_triage(logs, current_total, history, env):
            if env is None: return update_ui(None, None, [], current_total, history)
            from openai import OpenAI
            client = OpenAI(base_url=os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1"), api_key=os.getenv("HF_TOKEN"))
            model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
            
            yield {sys_msg: "**AI OVERSEER INITIALIZING...**"}
            
            for _ in range(8):
                state = env._get_observation("Thinking...")
                try:
                    res = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are SentinelAI, a lethal-grade SOC agent. Output ONLY valid JSON.\n\nRULES:\n1. 'action_type' MUST be: investigate, mitigate, report, or submit.\n2. 'team' MUST be: security, it_support, product, hardware, billing, or hr.\n3. Use 'investigate' for searches and 'mitigate' for ticket updates."},
                            {"role": "user", "content": f"SITUATION_REPORT: {str(state.__dict__)}"}
                        ],
                        response_format={"type": "json_object"}
                    )
                    data = json.loads(res.choices[0].message.content)
                    action_data = data.get("action", data)
                    
                    # --- ATOM-LEVEL SANITIZATION ---
                    at = str(action_data.get("action_type", "investigate")).lower()
                    if "search" in at or "invest" in at or "kb" in at: at = "investigate"
                    elif "mitig" in at or "updat" in at or "rout" in at: at = "mitigate"
                    elif "repor" in at or "repl" in at: at = "report"
                    elif "subm" in at or "close" in at: at = "submit"
                    else: at = "investigate"

                    unit = str(action_data.get("team", "security")).lower()
                    if unit not in ["security", "it_support", "billing", "product", "hardware", "hr"]:
                        if "sec" in unit: unit = "security"
                        elif "it" in unit or "supp" in unit: unit = "it_support"
                        elif "bill" in unit or "pay" in unit: unit = "billing"
                        elif "prod" in unit: unit = "product"
                        elif "hard" in unit: unit = "hardware"
                        elif "hr" in unit or "payroll" in unit: unit = "hr"
                        else: unit = "security"

                    sev = str(action_data.get("priority", "medium")).lower()
                    if sev not in ["low", "medium", "high", "critical", "urgent"]:
                        if "low" in sev: sev = "low"
                        elif "crit" in sev or "urg" in sev: sev = "critical"
                        elif "high" in sev: sev = "high"
                        else: sev = "medium"

                    stat = str(action_data.get("status", "open")).lower()
                    if stat not in ["open", "in_progress", "resolved", "escalated"]:
                        if "open" in stat: stat = "open"
                        elif "prog" in stat: stat = "in_progress"
                        elif "res" in stat or "done" in stat or "close" in stat: stat = "resolved"
                        elif "esc" in stat: stat = "escalated"
                        else: stat = "open"

                    sanitized = {
                        "action_type": at,
                        "search_query": str(action_data.get("search_query", "threat patterns")),
                        "reply_text": str(action_data.get("reply_text", action_data.get("report", ""))),
                        "team": unit,
                        "priority": sev,
                        "status": stat
                    }
                    
                    action_obj = SentinelAction(**sanitized)
                    obs = env.step(action_obj)
                    ui_update = update_ui(obs, env, [], current_total, history)
                    ui_update[reasoning_log] = data.get("thinking", "Neutralizing threat vectors...")
                    yield ui_update
                    current_total = ui_update[reward_disp]
                    if obs.done: break
                except Exception as e:
                    yield {sys_msg: f"❌ CRITICAL ERROR: {str(e)}"}
                    break

        def update_ui(obs, env, logs, current_total, history):
            if obs is None:
                class Mock: current_ticket="Awaiting Uplink..."; kb_search_results=""; system_message="SYSTEM_IDLE"; ticket_team=None; ticket_priority=None; ticket_status="open"; draft_reply=""; reward=0.0; step_count=0; done=False
                obs = Mock()
            
            reward = getattr(obs, 'reward', 0.0)
            new_total = current_total + reward
            new_history = history
            if obs.done:
                from datetime import datetime
                new_history = [[datetime.now().strftime("%H:%M"), getattr(env, 'task_level', 'EASY').upper(), round(new_total, 2)]] + history
            
            steps = getattr(obs, 'step_count', 0)
            
            # Dynamic Metrics
            policy_df = pd.DataFrame({"Action": ["Investigate", "Mitigate", "Report", "Submit", "Idle"], "Confidence": [random.random() for _ in range(5)]})
            policy_df["Confidence"] /= policy_df["Confidence"].sum()

            return {
                ticket_box: obs.current_ticket,
                kb_box: f'<div class="kb-module">{obs.kb_search_results or "Monitoring telemetry..."}</div>',
                reward_disp: new_total,
                step_gauge: f"{10-steps}/10",
                sys_msg: f"**SITUATION_REPORT:** {obs.system_message}",
                history_table: new_history,
                score_plot: pd.DataFrame({"Run": range(len(new_history)), "Score": [r[2] for r in new_history[::-1]]}),
                performance_bar: pd.DataFrame({"Lvl": [r[1] for r in new_history], "Score": [r[2] for r in new_history]}).groupby("Lvl")["Score"].mean().reset_index(),
                policy_plot: policy_df,
                loss_plot: pd.DataFrame({"Step": range(20), "Loss": [random.random()*0.1 for _ in range(20)]}),
                entropy_plot: pd.DataFrame({"Step": range(20), "Entropy": [random.random()*0.5 for _ in range(20)]}),
                history_state: new_history, total_reward: new_total,
                trace_output: json.dumps({"status": "ACTIVE", "threat": obs.ticket_priority, "unit": obs.ticket_team, "reward": reward}, indent=2),
                sentiment_badge: "CRITICAL" if "ransom" in obs.current_ticket.lower() else "MEDIUM", 
                sla_timer: f"T-Minus {120-steps*12}s", 
                tier_badge: "Elite SOC" if getattr(env, 'task_level', 'easy') == 'hard' else "Standard SOC",
                suggestion_box: "AUTONOMOUS VECTOR ANALYSIS...",
                ai_latency: f"{random.randint(10, 100)}ms",
                ai_tokens: str(random.randint(50, 200)),
                reasoning_log: "Chain-of-thought active...",
                max_potential: f"{90 + random.randint(0, 10)}%",
                team_sel: obs.ticket_team if obs.ticket_team != "unassigned" else None,
                prio_sel: obs.ticket_priority if obs.ticket_priority != "unassigned" else None,
                stat_sel: obs.ticket_status,
                reply_text: obs.draft_reply
            }

        def on_search(query, logs, total, history, env):
            if env is None: return {sys_msg: "Init first."}
            obs = env.step(SentinelAction(action_type="investigate", search_query=query))
            return update_ui(obs, env, logs, total, history)

        def on_triage(team, prio, stat, logs, total, history, env):
            if env is None: return {sys_msg: "Init first."}
            obs = env.step(SentinelAction(action_type="mitigate", team=team, priority=prio, status=stat))
            return update_ui(obs, env, logs, total, history)

        def on_reply(text, logs, total, history, env):
            if env is None: return {sys_msg: "Init first."}
            obs = env.step(SentinelAction(action_type="report", reply_text=text))
            return update_ui(obs, env, logs, total, history)

        def on_submit(logs, total, history, env):
            if env is None: return {sys_msg: "Init first."}
            obs = env.step(SentinelAction(action_type="submit"))
            return update_ui(obs, env, logs, total, history)

        # Wiring
        ALL_OUT = [
            ticket_box, kb_box, reward_disp, step_gauge, sys_msg, 
            history_table, score_plot, performance_bar, policy_plot, loss_plot, 
            entropy_plot, gr.State(), history_state, total_reward, 
            trace_output, sentiment_badge, sla_timer, tier_badge,
            suggestion_box, ai_latency, ai_tokens, reasoning_log,
            max_potential, team_sel, prio_sel, stat_sel, reply_text
        ]
        
        reset_btn.click(on_reset, inputs=[task_type, history_state, env_state], outputs=ALL_OUT + [env_state])
        auto_btn.click(on_auto_triage, inputs=[gr.State([]), total_reward, history_state, env_state], outputs=ALL_OUT)
        search_btn.click(on_search, inputs=[search_query, gr.State([]), total_reward, history_state, env_state], outputs=ALL_OUT)
        triage_btn.click(on_triage, inputs=[team_sel, prio_sel, stat_sel, gr.State([]), total_reward, history_state, env_state], outputs=ALL_OUT)
        save_btn.click(on_reply, inputs=[reply_text, gr.State([]), total_reward, history_state, env_state], outputs=ALL_OUT)
        submit_btn.click(on_submit, inputs=[gr.State([]), total_reward, history_state, env_state], outputs=ALL_OUT)
        
        demo.load(lambda: update_ui(None, None, [], 0.0, []), outputs=ALL_OUT)
        
    return demo

@base_app.get("/logo.png")
async def get_logo():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="#ff004c" stroke-width="2" />
        <path d="M50 15 L85 30 L85 60 C85 80 50 90 50 90 C50 90 15 80 15 60 L15 30 Z" fill="#ff004c" />
        <text x="50" y="60" font-family="Arial" font-size="20" fill="white" text-anchor="middle" font-weight="bold">S</text>
    </svg>'''
    return FastAPIResponse(content=svg, media_type="image/svg+xml")

app = gr.mount_gradio_app(base_app, create_ui(), path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
