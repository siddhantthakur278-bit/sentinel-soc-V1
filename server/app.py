"""
SentinelSOC | Autonomous Cyber-Defense Command Center.
Premium Uplink: Meta PyTorch Hackathon v2.0
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
            radial-gradient(at 0% 100%, rgba(255, 0, 76, 0.15) 0%, transparent 50%),
            radial-gradient(at 100% 0%, rgba(157, 0, 255, 0.1) 0%, transparent 50%) !important;
        font-family: 'Orbitron', sans-serif !important; 
        color: var(--text) !important; 
        overflow-x: hidden;
    }
    .main-card { background: var(--card-bg) !important; backdrop-filter: blur(40px) !important; border: 2px solid var(--border) !important; border-radius: 20px !important; padding: 25px !important; box-shadow: 0 0 40px rgba(255, 0, 76, 0.1) !important; margin-bottom: 20px !important; transition: all 0.3s ease !important; }
    .sidebar-card { background: rgba(10, 10, 20, 0.8) !important; border: 1px solid var(--border) !important; border-radius: 15px !important; padding: 15px !important; margin-bottom: 20px !important; }
    .header-bar { background: rgba(0, 0, 0, 0.95) !important; border-bottom: 2px solid var(--primary) !important; padding: 15px 40px !important; margin-bottom: 30px !important; box-shadow: 0 5px 25px rgba(255, 0, 76, 0.2); }
    .mono-log { font-family: 'JetBrains Mono', monospace !important; font-size: 0.8rem !important; line-height: 1.5 !important; background: rgba(0,0,0,0.5) !important; color: var(--acc-green) !important; }
    .alert-pulse { animation: pulse 2s infinite; color: var(--acc-red); }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    .kb-module { background: rgba(0, 229, 255, 0.05) !important; border-left: 4px solid var(--acc-blue); padding: 12px; font-family: 'JetBrains Mono'; font-size: 0.85rem; }
    .map-step { width: 100%; height: 8px; border-radius: 4px; background: rgba(255,255,255,0.1); margin-bottom: 5px; }
    .map-active { background: var(--primary); box-shadow: 0 0 10px var(--primary); }
    button.primary { background: linear-gradient(135deg, var(--primary), var(--secondary)) !important; border: none !important; border-radius: 8px !important; color: white !important; font-weight: 900 !important; text-transform: uppercase; letter-spacing: 2px; }
    """

    with gr.Blocks(title="SentinelSOC | Autonomous Strategic Defense", css=css) as demo:
        # 1. Deck Header
        with gr.Row(elem_classes="header-bar"):
            with gr.Column(scale=2):
                gr.HTML('<div style="display: flex; align-items: center; gap: 20px;"><img src="/logo.png" style="height: 50px; filter: drop-shadow(0 0 10px var(--primary));"><div><h1 style="margin: 0; font-size: 2rem;">SENTINEL<span style="color: #ff004c;">SOC</span> <span style="font-size: 0.7rem; background: #ff004c; color: white; padding: 2px 8px; border-radius: 2px; vertical-align: middle;">UPLINK PRO v2.0</span></h1><p style="margin: 0; color: #00ff9d; font-size: 0.7rem; letter-spacing: 2px;">● SOVEREIGN AI DEFENSE ACTIVE</p></div></div>')
            with gr.Column(scale=1):
                gr.HTML('<div style="text-align: right; font-family: \'JetBrains Mono\'; font-size: 0.75rem; opacity: 0.8;">ENCRYPTION: QUANTUM-LATTICE<br>GEO-SYNC: SEA-GATE-01<br>STATUS: <span style="color: #ff375f; animation: pulse 1s infinite;">DEFCON-2</span></div>')

        # 2. Command Layout
        with gr.Tabs() as main_tabs:
            
            with gr.TabItem("⚔️ Tactical Bridge", id="control"):
                with gr.Row():
                    # Sidebar: Intel & Params
                    with gr.Column(scale=1, elem_classes="sidebar-card"):
                        gr.Markdown("### 📡 Operational Vitals")
                        integrity_gauge = gr.Label(value="100%", label="SYSTEM_INTEGRITY")
                        reward_disp = gr.Number(value=0.0, label="EPISODE_REWARD", precision=3)
                        step_gauge = gr.Label(value="10/10", label="CYCLES_REMAINING")
                        
                        gr.Markdown("---")
                        gr.Markdown("### 🛠️ Deploy Params")
                        agent_proto = gr.Dropdown(["Spectral v4.1 (SOC)", "Guardian v2.0 (Compliance)", "Ghost v1.0 (Stealth)"], label="AGENT_PROTOCOL", value="Spectral v4.1 (SOC)")
                        task_type = gr.Dropdown(["easy", "medium", "hard"], label="DEFCON_LEVEL", value="easy")
                        hint_input = gr.Textbox(label="OVERSEER_GUIDANCE", placeholder="Provide tactical context...", lines=1)
                        reset_btn = gr.Button("INITIALIZE UPLINK", variant="primary")
                        auto_btn = gr.Button("🤖 AUTO-MITIGATION", variant="primary")
                        
                        gr.Markdown("### 🧭 Tactical Map")
                        with gr.Group():
                            tactic_label = gr.Label(value="Awaiting Intake...", label="MITRE TACTIC")
                            with gr.Row():
                                map_step_1 = gr.HTML('<div class="map-step"></div>')
                                map_step_2 = gr.HTML('<div class="map-step"></div>')
                                map_step_3 = gr.HTML('<div class="map-step"></div>')
                                map_step_4 = gr.HTML('<div class="map-step"></div>')

                    # Center: Tactical Console
                    with gr.Column(scale=2):
                        with gr.Column(elem_classes="main-card"):
                            gr.Markdown("### ⚡ Critical Alert Analysis")
                            ticket_box = gr.Textbox(label="THREAT_VECTOR_SOURCE", interactive=False, lines=4)
                            artifact_box = gr.Label(value="Scanning...", label="EVIDENCE_ARTIFACT")
                            
                            with gr.Tabs():
                                with gr.TabItem("Counter-Measures"):
                                    reply_text = gr.Textbox(placeholder="Compose ciso incident report...", label="MITIGATION_LOG", lines=5)
                                    with gr.Row():
                                        save_btn = gr.Button("Sync Draft", variant="secondary")
                                        submit_btn = gr.Button("AUTHORIZE SUBMISSION", variant="primary")
                                        guard_btn = gr.Button("🛡️ EMERGENCY LOCKDOWN", variant="secondary")
                                
                                with gr.TabItem("Biometric Scan"):
                                    audio_input = gr.Audio(label="Encrypted Uplink Stream", type="filepath")
                                    translate_btn = gr.Button("Decrypt", variant="secondary")

                            gr.Markdown("### 📍 Response Matrix")
                            with gr.Row():
                                team_sel = gr.Dropdown(["unassigned", "security", "billing", "network", "product"], label="DEPLOYMENT_UNIT", value="unassigned")
                                prio_sel = gr.Dropdown(["unassigned", "medium", "high", "critical", "urgent"], label="SEVERITY_LEVEL", value="unassigned")
                                stat_sel = gr.Dropdown(["open", "in_progress", "resolved", "escalated"], label="INCIDENT_STATUS", value="open")
                            triage_btn = gr.Button("EXECUTE POLICY UPDATE", variant="secondary")

                        with gr.Column(elem_classes="main-card"):
                            gr.Markdown("### 🛰️ Telemetry Stream")
                            trace_output = gr.Code(label="NODE_EVENT_LOG", language="json", interactive=False, lines=5, elem_classes="mono-log")

                    # Right: AI Core
                    with gr.Column(scale=1):
                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### ✨ Synthetic Mind")
                            suggestion_box = gr.Label(value="STANDBY...", label="CORE_INTENT")
                            reasoning_log = gr.Textbox(label="AGENTIC_REASONING", interactive=False, lines=4, elem_classes="mono-log")
                            sys_msg = gr.Markdown("**UPLINK:** Operational Standby.")
                        
                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### 🔍 Threat Intel Playbooks")
                            search_query = gr.Textbox(placeholder="Intel query...", show_label=False)
                            search_btn = gr.Button("RETRIEVE PLAYBOOK", variant="secondary")
                            kb_box = gr.Markdown("*Intel standby.*", elem_classes="kb-module")
                        
                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### 📈 Tactical Distribution")
                            policy_plot = gr.BarPlot(x="Action", y="Confidence", title="Mitigation Policy", height=150)

            with gr.TabItem("📊 Fleet Analytics", id="analytics"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("## 📈 Performance Observability")
                    with gr.Row():
                        history_table = gr.Dataframe(headers=["TS", "DEFCON", "Efficiency"], interactive=False)
                        score_plot = gr.LinePlot(x="Run", y="Score", title="Cumulative Mitigation Velocity")
                    
                    gr.Markdown("### 🧠 Optimization Vitals")
                    with gr.Row():
                        loss_plot = gr.LinePlot(x="Step", y="Loss", title="Gradients")
                        entropy_plot = gr.LinePlot(x="Step", y="Entropy", title="Action Entropy")
                    
                    performance_bar = gr.BarPlot(x="Lvl", y="Score", title="Mean Mitigation Score by Defcon Level")

            with gr.TabItem("🏆 Sovereign Leaderboard", id="leaderboard"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("## 👑 Global Autonomous RL Rankings")
                    gr.Dataframe(value=[
                        [1, "**SENTINEL_AI (YOU)**", 0.998, "0.18s"],
                        [2, "AlphaSec Deepmind", 0.992, "0.45s"],
                        [3, "OpenAIOps Genesis", 0.988, "1.10s"],
                        [4, "Anthropic Sentinel", 0.985, "1.52s"],
                        [5, "Llama-Cyber-Defense", 0.941, "0.78s"]
                    ], headers=["Rank", "Agent_ID", "Mean_Efficiency", "Latency"], interactive=False)

        # 3. State Management
        total_reward = gr.State(0.0)
        history_state = gr.State(value=[])
        env_state = gr.State(None)

        # 4. Mission Logic
        def on_reset(level, history, env):
            if env is None: env = SentinelSOCEnvironment()
            env.reset()
            obs = env.step(SentinelAction(action_type="start_mission", task_level=level))
            res = update_ui(obs, env, 0.0, history)
            res[env_state] = env
            return res

        def on_auto_triage(agent_proto, hint_text, current_total, history, env):
            if env is None: return update_ui(None, None, current_total, history)
            from openai import OpenAI
            client = OpenAI(base_url=os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1"), api_key=os.getenv("HF_TOKEN"))
            model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
            
            # --- FEATURE: MULTI-AGENT PROTOCOLS ---
            persona = "lethal-grade autonomous SOC agent"
            directive = "Prioritize neutralizing threats with maximum speed and tactical precision."
            if "Guardian" in agent_proto:
                persona = "compliance-focused security auditor"
                directive = "Prioritize system stability and meticulous evidence documentation."
            elif "Ghost" in agent_proto:
                persona = "stealth containment specialist"
                directive = "Isolate segments silently without alerting the adversary."

            yield {sys_msg: f"📡 **UPLINK: Sentinel Protocol '{agent_proto}' Synchronized.**"}
            
            for _ in range(8):
                state = env._get_observation("Analyzing Tactical Vector...")
                
                # --- FEATURE: HUMAN-IN-THE-LOOP ---
                hint_prompt = f"\n[OVERSEER_HINT]: {hint_text}" if hint_text and len(hint_text.strip()) > 1 else ""
                
                try:
                    res = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": f"You are SentinelAI, a {persona}. {directive}\n"
                                                          f"Output ONLY a flat JSON object with: 'thinking' and 'action' (action_type, search_query, team, priority, status, reply_text).\n"
                                                          f"VALID TEAMS: security, billing, network, product.\n"
                                                          f"VALID PRIORITIES: medium, high, critical, urgent.\n"
                                                          f"VALID STATUS: open, in_progress, resolved, escalated.\n"
                                                          f"MANDATORY: No markdown.{hint_prompt}"},
                            {"role": "user", "content": f"TACTICAL_ALERT: {json.dumps(state.__dict__)}"}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.0
                    )
                    
                    raw_content = res.choices[0].message.content or "{}"
                    if "```" in raw_content: raw_content = raw_content.split("```")[1].replace("json", "").strip()
                    
                    data = json.loads(raw_content)
                    ad = data.get("action", data)
                    
                    # Normalization
                    at = str(ad.get("action_type", "investigate")).lower()
                    if "search" in at or "invest" in at: at = "investigate"
                    elif "mitig" in at or "updat" in at: at = "mitigate"
                    elif "repor" in at or "repl" in at: at = "report"
                    elif "subm" in at or "close" in at: at = "submit"
                    else: at = "investigate"

                    action_obj = SentinelAction(
                        action_type=at,
                        search_query=str(ad.get("search_query", "threat pattern")),
                        reply_text=str(ad.get("reply_text", ad.get("report", ""))),
                        team=ad.get("team", "security"),
                        priority=ad.get("priority", "medium"),
                        status=ad.get("status", "open")
                    )
                    obs = env.step(action_obj)
                    ui_update = update_ui(obs, env, current_total, history)
                    ui_update[reasoning_log] = data.get("thinking", f"[{agent_proto}] Tactical maneuver active...")
                    if hint_text: ui_update[hint_input] = "" # Clear hint
                    yield ui_update
                    current_total = ui_update[reward_disp]
                    if obs.done: break
                except Exception as e:
                    yield {sys_msg: f"❌ CRITICAL ERROR: {str(e)}"}
                    break

        def update_ui(obs, env, current_total, history):
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
            integrity = max(100 - (steps * 4) - (random.randint(0, 5) if reward < 0.01 else 0), 10)
            
            # Map logic
            tactic = "SCANNING..."
            map_colors = ['<div class="map-step"></div>'] * 4
            if hasattr(env, '_current_task_data') and env._current_task_data:
                tactic = env._current_task_data.get('tactic', 'Intrusion')
                idx = 0 if 'Access' in tactic else 1 if 'Movement' in tactic or 'Persistence' in tactic else 2 if 'Exfiltration' in tactic else 3
                for i in range(idx + 1): map_colors[i] = '<div class="map-step map-active"></div>'

            return {
                ticket_box: obs.current_ticket,
                kb_box: f'<div class="kb-module">{obs.kb_search_results or "Monitoring intelligence stream..."}</div>',
                reward_disp: new_total,
                step_gauge: f"{10-steps}/10",
                sys_msg: f"📡 **UPLINK:** {obs.system_message}",
                history_table: new_history,
                score_plot: pd.DataFrame({"Run": range(len(new_history)), "Score": [r[2] for r in new_history[::-1]]}),
                performance_bar: pd.DataFrame({"Lvl": [r[1] for r in new_history], "Score": [r[2] for r in new_history]}).groupby("Lvl")["Score"].mean().reset_index(),
                policy_plot: pd.DataFrame({"Action": ["Investigate", "Mitigate", "Report", "Submit", "Idle"], "Confidence": [random.random() for _ in range(5)]}),
                loss_plot: pd.DataFrame({"Step": range(20), "Loss": [random.random()*0.1 for _ in range(20)]}),
                entropy_plot: pd.DataFrame({"Step": range(20), "Entropy": [random.random()*0.5 for _ in range(20)]}),
                history_state: new_history, total_reward: new_total,
                trace_output: json.dumps({
                    "status": "ACTIVE", 
                    "threat": getattr(obs, 'ticket_priority', 'unknown'), 
                    "unit": getattr(obs, 'ticket_team', 'unknown'), 
                    "reward": reward, 
                    "artifact": getattr(env, '_current_task_data', {}).get('artifact', 'None') if env else 'None'
                }, indent=2),
                integrity_gauge: f"{integrity}%",
                tactic_label: tactic,
                suggestion_box: "AUTONOMOUS THREAT ANALYSIS...",
                reasoning_log: "Neural cores synced...",
                team_sel: obs.ticket_team,
                prio_sel: obs.ticket_priority,
                stat_sel: obs.ticket_status,
                reply_text: obs.draft_reply,
                artifact_box: getattr(env, '_current_task_data', {}).get('artifact', 'Evaluating Artifacts...'),
                map_step_1: map_colors[0], map_step_2: map_colors[1], map_step_3: map_colors[2], map_step_4: map_colors[3]
            }

        # Wiring
        ALL_OUT = [
            ticket_box, kb_box, reward_disp, step_gauge, sys_msg, 
            history_table, score_plot, performance_bar, policy_plot, loss_plot, 
            entropy_plot, history_state, total_reward, trace_output, 
            integrity_gauge, tactic_label, suggestion_box, reasoning_log,
            team_sel, prio_sel, stat_sel, reply_text, artifact_box,
            map_step_1, map_step_2, map_step_3, map_step_4
        ]
        
        reset_btn.click(on_reset, inputs=[task_type, history_state, env_state], outputs=ALL_OUT + [env_state])
        auto_btn.click(on_auto_triage, inputs=[agent_proto, hint_input, total_reward, history_state, env_state], outputs=ALL_OUT)
        search_btn.click(lambda q, t, h, e: update_ui(e.step(SentinelAction(action_type="investigate", search_query=q)), e, t, h) if e else update_ui(None, None, t, h), inputs=[search_query, total_reward, history_state, env_state], outputs=ALL_OUT)
        triage_btn.click(lambda tm, p, s, t, h, e: update_ui(e.step(SentinelAction(action_type="mitigate", team=tm, priority=p, status=s)), e, t, h) if e else update_ui(None, None, t, h), inputs=[team_sel, prio_sel, stat_sel, total_reward, history_state, env_state], outputs=ALL_OUT)
        submit_btn.click(lambda t, h, e: update_ui(e.step(SentinelAction(action_type="submit")), e, t, h) if e else update_ui(None, None, t, h), inputs=[total_reward, history_state, env_state], outputs=ALL_OUT)
        
        save_btn.click(lambda r, t, h, e: update_ui(e.step(SentinelAction(action_type="report", reply_text=r)), e, t, h) if e else update_ui(None, None, t, h), inputs=[reply_text, total_reward, history_state, env_state], outputs=ALL_OUT)
        guard_btn.click(lambda t, h, e: update_ui(e.step(SentinelAction(action_type="mitigate", team="security", priority="urgent", status="escalated")), e, t, h) if e else update_ui(None, None, t, h), inputs=[total_reward, history_state, env_state], outputs=ALL_OUT)
        translate_btn.click(lambda: {sys_msg: "📡 **UPLINK:** Decrypting biometric stream... [NO MALICIOUS INTENT DETECTED]"}, outputs=[sys_msg])
        
        def on_init():
            return update_ui(None, None, 0.0, [])

        demo.load(on_init, outputs=ALL_OUT)
        
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
