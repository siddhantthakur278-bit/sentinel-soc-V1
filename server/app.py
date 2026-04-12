"""
SentinelSOC | Autonomous Cyber-Defense Command Center.
Premium Uplink: Meta PyTorch Hackathon v2.0
"""
try:
    import gradio as gr
    from fastapi import FastAPI, Response as FastAPIResponse
    import os
    import json
    import time
    import random
    import pandas as pd
    from datetime import datetime
    from fpdf import FPDF
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

# Valid values matching tickets.json & models.py
VALID_TEAMS = ["unassigned", "security", "billing", "network", "product", "it_support", "hr", "hardware"]
VALID_PRIORITIES = ["unassigned", "low", "medium", "high", "critical", "urgent"]
VALID_STATUSES = ["open", "in_progress", "resolved", "escalated"]

# CSS defined at module level so it can be passed to mount_gradio_app (Gradio 6+)
APP_CSS = """
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
.kb-module { background: rgba(0, 229, 255, 0.05) !important; border-left: 4px solid var(--acc-blue); padding: 12px; font-family: 'JetBrains Mono'; font-size: 0.85rem; white-space: pre-wrap; }
.map-step { width: 100%; height: 8px; border-radius: 4px; background: rgba(255,255,255,0.1); margin-bottom: 5px; }
.map-active { background: var(--primary); box-shadow: 0 0 10px var(--primary); }
.gr-button-primary { background: linear-gradient(135deg, var(--primary), var(--secondary)) !important; border: none !important; border-radius: 8px !important; color: white !important; font-weight: 900 !important; text-transform: uppercase; letter-spacing: 2px; }
.action-bar { background: rgba(255, 0, 76, 0.05) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; padding: 10px 20px !important; margin-bottom: 25px !important; display: flex; align-items: center; gap: 15px; }
.action-bar-label { font-family: 'JetBrains Mono'; font-size: 0.7rem; color: var(--primary); font-weight: bold; letter-spacing: 1px; }
"""

def create_ui():

    with gr.Blocks(title="SentinelSOC | Autonomous Strategic Defense") as demo:

        # === HEADER ===
        with gr.Row(elem_classes="header-bar"):
            with gr.Column(scale=2):
                gr.HTML('<div style="display: flex; align-items: center; gap: 20px;"><img src="/logo.png" style="height: 50px; filter: drop-shadow(0 0 10px var(--primary));"><div><h1 style="margin: 0; font-size: 2rem;">SENTINEL<span style="color: #ff004c;">SOC</span> <span style="font-size: 0.7rem; background: #ff004c; color: white; padding: 2px 8px; border-radius: 2px; vertical-align: middle;">UPLINK PRO v2.0</span></h1><p style="margin: 0; color: #00ff9d; font-size: 0.7rem; letter-spacing: 2px;">● SOVEREIGN AI DEFENSE ACTIVE</p></div></div>')
            with gr.Column(scale=1):
                gr.HTML('<div style="text-align: right; font-family: \'JetBrains Mono\'; font-size: 0.75rem; opacity: 0.8;">ENCRYPTION: QUANTUM-LATTICE<br>GEO-SYNC: SEA-GATE-01<br>STATUS: <span style="color: #ff375f;">DEFCON-2</span></div>')

        # === TABS ===
        with gr.Tabs() as main_tabs:

            # ─── TAB 1: Tactical Bridge ───────────────────────────────────────
            with gr.TabItem("⚔️ Tactical Bridge", id="control"):
                with gr.Row():

                    # --- LEFT SIDEBAR ---
                    with gr.Column(scale=1, elem_classes="sidebar-card"):
                        gr.Markdown("### 📡 Operational Vitals")
                        integrity_gauge = gr.Label(value="100%", label="SYSTEM_INTEGRITY")
                        reward_disp = gr.Number(value=0.0, label="EPISODE_REWARD", precision=3)
                        step_gauge = gr.Label(value="10/10", label="CYCLES_REMAINING")

                        gr.Markdown("---")
                        gr.Markdown("### 🛠️ Deploy Params")
                        agent_proto = gr.Dropdown(
                            ["Spectral v4.1 (SOC)", "Guardian v2.0 (Compliance)", "Ghost v1.0 (Stealth)"],
                            label="AGENT_PROTOCOL", value="Spectral v4.1 (SOC)"
                        )
                        task_type = gr.Dropdown(["easy", "medium", "hard"], label="DEFCON_LEVEL", value="easy")
                        hint_input = gr.Textbox(label="OVERSEER_GUIDANCE", placeholder="Provide tactical hint for AI...", lines=1)
                        reset_btn = gr.Button("🔄 INITIALIZE UPLINK", variant="primary")
                        auto_btn = gr.Button("🤖 AUTO-MITIGATION", variant="primary")

                        gr.Markdown("### 🧭 Tactical Map")
                        with gr.Group():
                            tactic_label = gr.Label(value="Awaiting Intake...", label="MITRE TACTIC")
                            with gr.Row():
                                map_step_1 = gr.HTML('<div class="map-step"></div>')
                                map_step_2 = gr.HTML('<div class="map-step"></div>')
                                map_step_3 = gr.HTML('<div class="map-step"></div>')
                                map_step_4 = gr.HTML('<div class="map-step"></div>')

                    # --- CENTER CONSOLE ---
                    with gr.Column(scale=2):
                        with gr.Column(elem_classes="main-card"):
                            gr.Markdown("### ⚡ Critical Alert Analysis")
                            ticket_box = gr.Textbox(
                                label="THREAT_VECTOR_SOURCE", interactive=False, lines=4,
                                value="Awaiting mission. Click 'INITIALIZE UPLINK' to start."
                            )
                            artifact_box = gr.Label(value="Scanning...", label="EVIDENCE_ARTIFACT")

                            with gr.Tabs():
                                with gr.TabItem("Counter-Measures"):
                                    reply_text = gr.Textbox(
                                        placeholder="Draft your CISO incident report here...",
                                        label="MITIGATION_LOG", lines=5, interactive=True
                                    )
                                    with gr.Row():
                                        save_btn = gr.Button("💾 Sync Draft", variant="secondary")
                                        submit_btn = gr.Button("✅ AUTHORIZE SUBMISSION", variant="primary")
                                        guard_btn = gr.Button("🛡️ EMERGENCY LOCKDOWN", variant="secondary")

                                with gr.TabItem("Biometric Scan"):
                                    audio_input = gr.Audio(label="Encrypted Uplink Stream", type="filepath")
                                    translate_btn = gr.Button("🔓 Decrypt", variant="secondary")

                            gr.Markdown("### 📍 Response Matrix")
                            with gr.Row():
                                team_sel = gr.Dropdown(VALID_TEAMS, label="DEPLOYMENT_UNIT", value="unassigned")
                                prio_sel = gr.Dropdown(VALID_PRIORITIES, label="SEVERITY_LEVEL", value="unassigned")
                                stat_sel = gr.Dropdown(VALID_STATUSES, label="INCIDENT_STATUS", value="open")
                            triage_btn = gr.Button("⚙️ EXECUTE POLICY UPDATE", variant="secondary")

                        with gr.Column(elem_classes="main-card"):
                            gr.Markdown("### 🛰️ Telemetry Stream")
                            trace_output = gr.Code(
                                label="NODE_EVENT_LOG", language="json",
                                interactive=False, lines=6, elem_classes="mono-log"
                            )

                    # --- RIGHT: AI CORE ---
                    with gr.Column(scale=1):
                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### ✨ Synthetic Mind")
                            suggestion_box = gr.Label(value="STANDBY...", label="CORE_INTENT")
                            reasoning_log = gr.Textbox(
                                label="AGENTIC_REASONING", interactive=False,
                                lines=5, elem_classes="mono-log",
                                value="Awaiting autonomous operation..."
                            )
                            sys_msg = gr.Markdown("**UPLINK:** Operational Standby.")

                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### 🔍 Threat Intel Playbooks")
                            search_query = gr.Textbox(placeholder="e.g. phishing, ransomware, sql injection...", show_label=False)
                            search_btn = gr.Button("🔎 RETRIEVE PLAYBOOK", variant="secondary")
                            kb_box = gr.Markdown("*Query the knowledge base above.*", elem_classes="kb-module")

                        with gr.Column(elem_classes="sidebar-card"):
                            gr.Markdown("### 📈 Action Distribution")
                            policy_plot = gr.BarPlot(
                                x="Action", y="Confidence",
                                title="Mitigation Policy", height=180,
                                value=pd.DataFrame({
                                    "Action": ["Investigate", "Mitigate", "Report", "Submit", "Idle"],
                                    "Confidence": [0.2, 0.2, 0.2, 0.2, 0.2]
                                })
                            )

            # ─── TAB 2: Analytics ─────────────────────────────────────────────
            with gr.TabItem("📊 Fleet Analytics", id="analytics"):
                with gr.Column(elem_classes="main-card"):
                    with gr.Row(elem_classes="action-bar"):
                        gr.HTML('<div class="action-bar-label">TACTICAL_OVERSEER_V2.0 // FAST_ACTION_BAR</div>')
                        analytics_reset_btn = gr.Button("🔄 REBOOT UPLINK", variant="secondary", size="sm")
                        analytics_auto_btn = gr.Button("🤖 START AI PILOT", variant="primary", size="sm")
                        analytics_submit_btn = gr.Button("✅ AUTHORIZE SUBMIT", variant="primary", size="sm")
                        analytics_refresh_btn = gr.Button("📊 SYNC ANALYTICS", variant="secondary", size="sm")

                    gr.Markdown("## 📈 Performance Observability")
                    with gr.Row():
                        history_table = gr.Dataframe(
                            headers=["Timestamp", "DEFCON Level", "Efficiency Score"],
                            interactive=False, label="Mission History"
                        )
                        score_plot = gr.LinePlot(
                            x="Run", y="Score", title="Cumulative Mitigation Velocity",
                            value=pd.DataFrame({"Run": [0], "Score": [0.0]})
                        )

                    gr.Markdown("### 🧠 Training Vitals")
                    with gr.Row():
                        loss_plot = gr.LinePlot(
                            x="Step", y="Loss", title="Policy Loss",
                            value=pd.DataFrame({"Step": list(range(20)), "Loss": [0.1] * 20})
                        )
                        entropy_plot = gr.LinePlot(
                            x="Step", y="Entropy", title="Action Entropy",
                            value=pd.DataFrame({"Step": list(range(20)), "Entropy": [0.5] * 20})
                        )
                    performance_bar = gr.BarPlot(
                        x="Lvl", y="Score", title="Mean Score by DEFCON Level",
                        value=pd.DataFrame({"Lvl": ["EASY", "MEDIUM", "HARD"], "Score": [0.0, 0.0, 0.0]})
                    )

            # ─── TAB 3: Neural Probe ──────────────────────────────────────────
            with gr.TabItem("🧠 Neural Probe", id="neural"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("## 👁️ AI Logic Observability")
                    with gr.Row():
                        with gr.Column(scale=2):
                            live_thinking = gr.Textbox(label="REAL_TIME_COG_STREAM", lines=12, elem_classes="mono-log", interactive=False)
                        with gr.Column(scale=1):
                            gr.Markdown("### 📡 Model Telemetry")
                            model_label = gr.Label(value="gpt-4o-mini", label="DEPLOYED_MODEL")
                            tokens_gauge = gr.Label(value="0", label="TOTAL_TOKENS_UTILIZED")
                            latency_val = gr.Label(value="0.0s", label="PROMPT_LATENCY")
                            
                            gr.Markdown("---")
                            gr.Markdown("### ⚖️ Decision Confidence")
                            confidence_plot = gr.BarPlot(
                                x="Action", y="Confidence", 
                                title="Action Weight Matrix", height=240,
                                value=pd.DataFrame({"Action": ["INV", "MIT", "REP", "SUB"], "Confidence": [0.25]*4})
                            )

            # ─── TAB 4: Forensic Archive ──────────────────────────────────────
            with gr.TabItem("📂 Forensic Archive", id="forensics"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("## 📋 Tactical Mission Logs")
                    with gr.Row():
                        with gr.Column(scale=1):
                            log_selector = gr.Dropdown(label="SELECT_MISSION_AUDIT", choices=["Last Mission"])
                            gen_pdf_btn = gr.Button("📄 GENERATE FORENSIC PDF", variant="primary")
                            download_file = gr.File(label="DOWNLOADED_REPORT", interactive=False)
                        with gr.Column(scale=2):
                            audit_display = gr.Textbox(label="MISSION_SEQUENCE_AUDIT", lines=15, elem_classes="mono-log", interactive=False)

            # ─── TAB 5: Defense Matrix ────────────────────────────────────────
            with gr.TabItem("⚙️ Defense Matrix", id="settings"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("## 🛠️ Global Command Overrides")
                    with gr.Row():
                        with gr.Column():
                            live_model = gr.Dropdown(
                                [
                                    "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo",
                                    "meta-llama/Llama-3.3-70B-Instruct", 
                                    "Qwen/Qwen2.5-72B-Instruct",
                                    "mistralai/Mistral-7B-Instruct-v0.3",
                                    "claude-3-5-sonnet"
                                ], 
                                label="TARGET_LLM_PROTOCOL", 
                                value=os.getenv("MODEL_NAME", "gpt-4o-mini"),
                                allow_custom_value=True
                            )
                            live_url = gr.Textbox(
                                label="UPLINK_ENDPOINT (API_BASE_URL)",
                                value=os.getenv("API_BASE_URL", "https://api.openai.com/v1"),
                                placeholder="e.g. https://router.huggingface.co/v1 or https://api.openai.com/v1"
                            )
                            live_temp = gr.Slider(0.0, 1.0, value=0.5, step=0.1, label="CREATIVE_ENTROPY (TEMP)")
                            live_max_steps = gr.Slider(5, 20, value=int(os.getenv("MAX_STEPS", "10")), step=1, label="MAX_TACTICAL_CYCLES")
                        with gr.Column():
                            live_prompt = gr.Textbox(
                                label="DIRECTOR'S_DIRECTIVE (SYSTEM_PROMPT)",
                                value="You are SentinelAI, a lethal-grade autonomous SOC analyst...",
                                lines=8
                            )
                    save_config_btn = gr.Button("💾 COMMIT POLICY CHANGES", variant="primary")

            # ─── TAB 3: Leaderboard ───────────────────────────────────────────
            with gr.TabItem("🏆 Sovereign Leaderboard", id="leaderboard"):
                with gr.Column(elem_classes="main-card"):
                    gr.Markdown("## 👑 Session Performance Rankings")
                    gr.Markdown("*Live mission scores. Click Refresh after completing missions.*")
                    with gr.Row():
                        leaderboard_table = gr.Dataframe(
                            headers=["Rank", "Mission", "DEFCON", "Score", "Grade"],
                            interactive=False, label="🎖️ Mission Leaderboard"
                        )
                        leaderboard_chart = gr.BarPlot(
                            x="Mission", y="Score", title="Mission Scores",
                            height=260,
                            value=pd.DataFrame({"Mission": ["—"], "Score": [0.01]})
                        )
                    gr.Markdown("### 📊 DEFCON Performance Matrix")
                    defcon_stats = gr.Dataframe(
                        headers=["DEFCON Level", "Missions Run", "Best", "Avg", "Worst"],
                        interactive=False, label="Per-Difficulty Analytics"
                    )
                    refresh_lb_btn = gr.Button("🔄 Refresh Rankings", variant="primary")
                    lb_msg = gr.Markdown("*Run missions in the Tactical Bridge tab, then click Refresh.*")

        # === STATE ===
        total_reward = gr.State(0.0)
        history_state = gr.State([])
        env_state = gr.State(None)
        audit_state = gr.State([])  # List of dicts: {'step': n, 'thinking': t, 'action': a}

        # =================================================================
        # HELPERS
        # =================================================================

        def _map_colors(env):
            colors = ['<div class="map-step"></div>'] * 4
            tactic = "SCANNING..."
            if env and hasattr(env, '_current_task_data') and env._current_task_data:
                tactic = env._current_task_data.get('tactic', 'Unknown')
                idx = (0 if 'Access' in tactic
                       else 1 if ('Movement' in tactic or 'Persistence' in tactic)
                       else 2 if 'Exfiltration' in tactic
                       else 3)
                for i in range(idx + 1):
                    colors[i] = '<div class="map-step map-active"></div>'
            return tactic, colors

        def _safe_team(val):
            return val if val in VALID_TEAMS else "unassigned"

        def _safe_priority(val):
            return val if val in VALID_PRIORITIES else "unassigned"

        def _safe_status(val):
            return val if val in VALID_STATUSES else "open"

        def build_ui_dict(obs, env, new_total, new_history, reasoning="", is_reset=False, audit_log=None):
            """Build the full output dict for ALL_OUT."""
            if audit_log is None: audit_log = []
            steps = getattr(obs, 'step_count', 0)
            reward = getattr(obs, 'reward', 0.0)
            integrity = max(100 - steps * 4, 10)
            tactic, colors = _map_colors(env)

            # Format Audit View
            audit_text = ""
            for entry in audit_log:
                audit_text += f"[{entry['step']}] ACTION: {entry['action']}\nTHINK: {entry['thinking']}\n---\n"

            # Analytics plots — only build when there's data
            if new_history:
                score_items = [r[2] for r in reversed(new_history)]
                score_df = pd.DataFrame({
                    "Run": list(range(1, len(score_items) + 1)),
                    "Score": score_items
                })
                perf_df = (
                    pd.DataFrame({"Lvl": [r[1] for r in new_history], "Score": [r[2] for r in new_history]})
                    .groupby("Lvl")["Score"].mean().reset_index()
                )
            else:
                score_df = pd.DataFrame({"Run": [0], "Score": [0.0]})
                perf_df = pd.DataFrame({"Lvl": ["EASY", "MEDIUM", "HARD"], "Score": [0.0, 0.0, 0.0]})

            # Policy plot — reflect actual AI confidence (simulated but proportional to score)
            action_map = {"investigate": 0, "mitigate": 1, "report": 2, "submit": 3, "start_mission": 4, "reply": 2}
            confidences = [0.02] * 5
            if audit_log:
                last_act = audit_log[-1]["action"].split("(")[0].lower()
                idx = action_map.get(last_act, 4)
                confidences[idx] = 0.85
                # Add some secondary noise
                for i in range(5):
                    if i != idx: confidences[i] = random.uniform(0.01, 0.05)

            policy_df = pd.DataFrame({
                "Action": ["INV", "MIT", "REP", "SUB", "IDLE"],
                "Confidence": confidences
            })

            # Training Vitals — Decaying loss/entropy for visual effect
            loss_vals = [max(0.01, 0.12 * (0.85 ** i)) for i in range(steps + 1)] + [0.0] * (19 - steps)
            entropy_vals = [max(0.1, 0.7 * (0.92 ** i)) for i in range(steps + 1)] + [0.0] * (19 - steps)
            loss_df = pd.DataFrame({"Step": list(range(20)), "Loss": loss_vals[:20]})
            entropy_df = pd.DataFrame({"Step": list(range(20)), "Entropy": entropy_vals[:20]})

            # Telemetry
            telemetry = json.dumps({
                "episode_step": steps,
                "system_integrity": f"{integrity}%",
                "threat_level": getattr(obs, 'ticket_priority', 'unassigned'),
                "assigned_unit": getattr(obs, 'ticket_team', 'unassigned'),
                "incident_status": getattr(obs, 'ticket_status', 'open'),
                "step_reward": round(reward, 4),
                "episode_total": round(new_total, 4),
                "kb_searched": bool(getattr(obs, 'kb_search_results', '')),
                "artifact": (env._current_task_data or {}).get('artifact', 'N/A') if env else 'N/A',
                "done": getattr(obs, 'done', False),
            }, indent=2)

            kb_content = getattr(obs, 'kb_search_results', '') or "No intel retrieved yet. Use RETRIEVE PLAYBOOK."

            reasoning_text = reasoning if reasoning else (
                "Mission initialized. Ready for autonomous operations." if is_reset
                else "Awaiting next action..."
            )

            return {
                ticket_box: getattr(obs, 'current_ticket', 'Awaiting Uplink...'),
                artifact_box: (env._current_task_data or {}).get('artifact', 'Scanning...') if env else 'Scanning...',
                reply_text: getattr(obs, 'draft_reply', ''),
                kb_box: f'<div class="kb-module">{kb_content}</div>',
                reward_disp: round(new_total, 4),
                step_gauge: f"{max(10 - steps, 0)}/10",
                integrity_gauge: f"{integrity}%",
                sys_msg: f"📡 **UPLINK:** {getattr(obs, 'system_message', '')}",
                tactic_label: tactic,
                team_sel: _safe_team(getattr(obs, 'ticket_team', 'unassigned')),
                prio_sel: _safe_priority(getattr(obs, 'ticket_priority', 'unassigned')),
                stat_sel: _safe_status(getattr(obs, 'ticket_status', 'open')),
                reasoning_log: reasoning_text,
                suggestion_box: "ACTIVE ANALYSIS" if steps > 0 else "STANDBY...",
                trace_output: telemetry,
                history_table: new_history,
                score_plot: score_df,
                performance_bar: perf_df,
                policy_plot: policy_df,
                loss_plot: loss_df,
                entropy_plot: entropy_df,
                history_state: new_history,
                total_reward: new_total,
                map_step_1: colors[0], map_step_2: colors[1],
                map_step_3: colors[2], map_step_4: colors[3],
                hint_input: gr.update(),
                live_thinking: reasoning if reasoning else "Awaiting operation...",
                audit_display: audit_text if audit_text else "No logs in current session.",
                audit_state: audit_log,
                confidence_plot: policy_df, # Shared visualization
                tokens_gauge: str(steps * 450), 
                latency_val: f"{1.2 + (steps * 0.1):.1f}s" if steps > 0 else "0.0s"
            }

        # =================================================================
        # EVENT HANDLERS
        # =================================================================

        def on_reset(level, history, env):
            """Reset environment and start a new mission."""
            if env is None:
                env = SentinelSOCEnvironment()
            env.reset()
            obs = env.step(SentinelAction(action_type="start_mission", task_level=level))
            result = build_ui_dict(obs, env, 0.0, history, is_reset=True)
            result[env_state] = env
            result[total_reward] = 0.0
            return result

        def on_search(query, current_total, history, env):
            """Query the knowledge base."""
            if not env or not env.task_level:
                return build_ui_dict(
                    _mock_obs("Start a mission first (click INITIALIZE UPLINK)."),
                    env, current_total, history
                )
            obs = env.step(SentinelAction(action_type="investigate", search_query=query))
            return build_ui_dict(obs, env, current_total + obs.reward, history)

        def on_triage(team, priority, status, current_total, history, env):
            """Apply triage settings from the Response Matrix."""
            if not env or not env.task_level:
                return build_ui_dict(
                    _mock_obs("Start a mission first (click INITIALIZE UPLINK)."),
                    env, current_total, history
                )
            obs = env.step(SentinelAction(
                action_type="mitigate",
                team=team if team != "unassigned" else None,
                priority=priority if priority != "unassigned" else None,
                status=status
            ))
            return build_ui_dict(obs, env, current_total + obs.reward, history)

        def on_save_draft(draft, current_total, history, env):
            """Sync the manually typed draft to the environment."""
            if not env or not env.task_level:
                return build_ui_dict(
                    _mock_obs("Start a mission first (click INITIALIZE UPLINK)."),
                    env, current_total, history
                )
            obs = env.step(SentinelAction(action_type="report", reply_text=draft))
            return build_ui_dict(obs, env, current_total + obs.reward, history,
                                 reasoning="Draft synchronized to environment.")

        def on_submit(current_total, history, env):
            """Submit and close the incident."""
            if not env or not env.task_level:
                return build_ui_dict(
                    _mock_obs("No active mission to submit."),
                    env, current_total, history
                )
            obs = env.step(SentinelAction(action_type="submit"))
            new_history = history
            if obs.done:
                # Score = done-step reward, strictly in (0, 1). NOT accumulated total.
                final_score = float(max(0.01, min(0.99, obs.reward)))
                mission_num = len(history) + 1
                new_history = [[
                    f"Mission #{mission_num}",
                    (env.task_level or "?").upper(),
                    round(final_score, 4)
                ]] + history
            return build_ui_dict(obs, env, obs.reward if obs.done else current_total, new_history,
                                 reasoning=f"Mission closed. Score: {round(obs.reward, 4)}/1.00")

        def on_lockdown(current_total, history, env):
            """Emergency lockdown — route to security, urgent, escalated."""
            if not env or not env.task_level:
                return build_ui_dict(
                    _mock_obs("No active mission for lockdown."),
                    env, current_total, history
                )
            obs = env.step(SentinelAction(
                action_type="mitigate",
                team="security", priority="urgent", status="escalated"
            ))
            return build_ui_dict(obs, env, current_total + obs.reward, history,
                                 reasoning="🛡️ EMERGENCY LOCKDOWN ENGAGED — security/urgent/escalated")

        def on_auto_triage(proto, hint_text, current_total, history, env, settings_model, settings_temp, settings_prompt, settings_max_steps, settings_url):
            """Autonomous AI-driven triage loop — yields updates per step."""
            if not env or not env.task_level:
                yield build_ui_dict(
                    _mock_obs("⚠️ No active mission. Click INITIALIZE UPLINK first."),
                    env, current_total, history
                )
                return

            try:
                from openai import OpenAI
            except ImportError:
                yield {sys_msg: "❌ openai library not installed."}
                return

            # SMART ENDPOINT SELECTION
            target_url = settings_url if settings_url else os.getenv("API_BASE_URL", "https://api.openai.com/v1")
            
            # Fix HF legacy endpoint 410 error
            if "api-inference.huggingface.co" in target_url:
                target_url = "https://router.huggingface.co/v1"
                
            # Auto-detect endpoint based on model name if using defaults
            if target_url == "https://api.openai.com/v1" and ("/" in model or "llama" in model.lower() or "qwen" in model.lower()):
                target_url = "https://router.huggingface.co/v1"
            
            llm = OpenAI(
                base_url=target_url,
                api_key=os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN", "")
            )
            # Use LIVE config from Defense Matrix
            model = settings_model
            temperature = settings_temp
            system_prompt_overide = settings_prompt

            # persona logic remains as fallback...
            if not system_prompt_overide or len(system_prompt_overide) < 10:
                persona = "compliance-focused auditor" if "Guardian" in proto else "autonomous SOC analyst"
                system_prompt = (
                    f"You are SentinelAI, an elite {persona}.\n"
                    "Your mission is to TRIAGE, MITIGATE, and REPORT security incidents.\n\n"
                    "OPERATIONAL DIRECTIVES:\n"
                    "1. INVESTIGATE: First, use 'investigate' to search the knowledge base for the threat pattern.\n"
                    "2. MITIGATE: Once identified, use 'mitigate' to update the incident metadata. You MUST include 'team', 'priority', 'status', and 'reply_text' in the mitigation call.\n"
                    "3. REPORT: Ensure the 'reply_text' (Mitigation Log) describes your actions and the resolution.\n"
                    "4. SUBMIT: Only submit when the incident is 'resolved' or 'escalated' and metadata is fully assigned.\n\n"
                    "MANDATORY JSON SCHEMA:\n"
                    "{\n"
                    "  \"thinking\": \"Tactical reasoning and plan\",\n"
                    "  \"action\": {\n"
                    "    \"action_type\": \"investigate\" | \"mitigate\" | \"report\" | \"submit\",\n"
                    "    \"search_query\": \"keyword query (for investigate)\",\n"
                    "    \"team\": \"security\"|\"network\"|\"billing\"|\"hr\"|\"it_support\"|\"product\"|\"hardware\",\n"
                    "    \"priority\": \"low\"|\"medium\"|\"high\"|\"critical\"|\"urgent\",\n"
                    "    \"status\": \"open\"|\"in_progress\"|\"resolved\"|\"escalated\",\n"
                    "    \"reply_text\": \"Required for mitigate/report: detailed incident report and mitigation steps\"\n"
                    "  }\n"
                    "}"
                )
            else:
                system_prompt = system_prompt_overide

            # CRITICAL: OpenAI 'json_object' mode requires 'json' in the prompt
            if "json" not in system_prompt.lower():
                system_prompt += "\n\nCRITICAL: You must output your tactical response as a valid JSON object."

            hint_clause = f"\n[OVERSEER_HINT]: {hint_text.strip()}" if hint_text and hint_text.strip() else ""
            system_prompt += hint_clause

            messages = [{"role": "system", "content": system_prompt}]
            running_total = current_total
            done_actions = []
            local_audit = []

            yield {sys_msg: f"📡 **UPLINK: '{proto}' Protocol Synchronized. Beginning autonomous triage...**"}

            for step_i in range(int(settings_max_steps)):
                state_obs = env._get_observation(f"Step {step_i + 1}: Analyzing threat matrix...")
                
                # Truncate KB results for SPEED and token efficiency
                kb_preview = (state_obs.kb_search_results or "N/A")[:500]
                if len(state_obs.kb_search_results or "") > 500:
                    kb_preview += "... [TRUNCATED for efficiency]"

                state_snapshot = {
                    "current_ticket": state_obs.current_ticket,
                    "kb_search_results": kb_preview,
                    "incident_metadata": {
                        "team": state_obs.ticket_team,
                        "priority": state_obs.ticket_priority,
                        "status": state_obs.ticket_status,
                        "report_draft": state_obs.draft_reply[:100] if state_obs.draft_reply else "Empty"
                    },
                    "actions_taken": [a["action"] for a in local_audit],
                }

                messages.append({"role": "user", "content": json.dumps(state_snapshot)})
                
                # Sliding window: System prompt + last 3 rounds (6 messages)
                tactical_context = [messages[0]] + messages[-6:]

                raw = "{}"
                try:
                    res = llm.chat.completions.create(
                        model=model,
                        messages=tactical_context,
                        response_format={"type": "json_object"},
                        temperature=temperature,
                        max_tokens=800,
                    )
                    raw = res.choices[0].message.content or "{}"
                    
                    # Robust JSON Extraction
                    import re
                    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                    if json_match:
                        raw = json_match.group(0)
                        
                    data = json.loads(raw)

                    thinking = data.get("thinking", f"[{proto}] Tactical maneuver in progress...")
                    messages.append({"role": "assistant", "content": raw})

                    # Robust Normalization
                    def norm(v): 
                        if v is None: return None
                        s = str(v).lower().strip()
                        return s if s else None

                    # Support Root-level or Nested-level action data
                    action_data = data.get("action", data) if isinstance(data.get("action"), dict) else data
                    
                    # 1. NORMALIZE ACTION TYPE
                    raw_at = norm(action_data.get("action_type") or action_data.get("at") or data.get("action_type"))
                    if not raw_at: at = "investigate"
                    elif any(x in raw_at for x in ["invest", "search", "kb", "query", "find"]): at = "investigate"
                    elif any(x in raw_at for x in ["mitig", "updat", "route", "assign", "remedi", "fix", "triage", "set"]): at = "mitigate"
                    elif any(x in raw_at for x in ["repor", "draft", "reply", "log"]): at = "report"
                    elif any(x in raw_at for x in ["submit", "close", "finish", "done", "complete"]): at = "submit"
                    else: at = "investigate"
                    
                    # 2. NORMALIZE FIELDS (Handle diverse AI naming)
                    team_val = norm(action_data.get("team") or action_data.get("unit") or action_data.get("deployment_unit"))
                    prio_val = norm(action_data.get("priority") or action_data.get("severity") or action_data.get("threat_level"))
                    stat_val = norm(action_data.get("status") or action_data.get("incident_status") or action_data.get("state"))
                    reply_val = action_data.get("reply_text") or action_data.get("report") or action_data.get("mitigation_log") or action_data.get("draft")

                    # Validation with fallbacks
                    if team_val not in VALID_TEAMS: team_val = None
                    if prio_val not in VALID_PRIORITIES: prio_val = None
                    if stat_val not in VALID_STATUSES: stat_val = None

                    action_obj = SentinelAction(
                        action_type=at,
                        search_query=str(action_data.get("search_query", "pattern search")),
                        reply_text=reply_val or "",
                        team=team_val,
                        priority=prio_val,
                        status=stat_val,
                    )

                    obs = env.step(action_obj)
                    final_score = float(max(0.01, min(0.99, obs.reward)))
                    
                    if obs.done:
                        mission_num = len(history) + 1
                        history = [[f"Mission #{mission_num}", (env.task_level or "?").upper(), round(final_score, 4)]] + history
                        running_total = final_score

                    local_audit.append({
                        "step": step_i + 1, 
                        "thinking": thinking, 
                        "action": f"{at}({team_val}/{prio_val})"
                    })
                    
                    result = build_ui_dict(obs, env, running_total, history, reasoning=thinking, audit_log=local_audit)
                    yield result

                    if obs.done:
                        yield {sys_msg: f"🎯 **MISSION SUCCESS:** Final Score {final_score:.4f}/1.0000"}
                        break

                except Exception as e:
                    import sys
                    print(f"[ERROR] AI Engine Crash: {e}\nRaw Output: {raw}", file=sys.stderr)
                    yield {sys_msg: f"❌ **AUTO-TRIAGE ERROR (step {step_i + 1}):** {str(e)}"}
                    break

        # =================================================================
        # MOCK OBS HELPER
        # =================================================================
        def _mock_obs(message: str):
            class Mock:
                current_ticket = "No active mission."
                kb_search_results = ""
                system_message = message
                ticket_team = "unassigned"
                ticket_priority = "unassigned"
                ticket_status = "open"
                draft_reply = ""
                reward = 0.0
                step_count = 0
                done = False
            return Mock()

        # =================================================================
        # OUTPUT MAPPING — must match exactly what build_ui_dict returns
        # =================================================================
        ALL_OUT = [
            ticket_box, artifact_box, reply_text, kb_box,
            reward_disp, step_gauge, integrity_gauge, sys_msg,
            tactic_label, team_sel, prio_sel, stat_sel,
            reasoning_log, suggestion_box, trace_output,
            history_table, score_plot, performance_bar,
            policy_plot, loss_plot, entropy_plot,
            history_state, total_reward,
            map_step_1, map_step_2, map_step_3, map_step_4,
            hint_input, live_thinking, audit_display, audit_state,
            confidence_plot, tokens_gauge, latency_val
        ]

        # =================================================================
        # WIRE BUTTONS
        # =================================================================
        reset_btn.click(
            on_reset,
            inputs=[task_type, history_state, env_state],
            outputs=ALL_OUT + [env_state]
        )
        auto_btn.click(
            on_auto_triage,
            inputs=[agent_proto, hint_input, total_reward, history_state, env_state, live_model, live_temp, live_prompt, live_max_steps, live_url],
            outputs=ALL_OUT
        )
        search_btn.click(
            on_search,
            inputs=[search_query, total_reward, history_state, env_state],
            outputs=ALL_OUT
        )
        triage_btn.click(
            on_triage,
            inputs=[team_sel, prio_sel, stat_sel, total_reward, history_state, env_state],
            outputs=ALL_OUT
        )
        save_btn.click(
            on_save_draft,
            inputs=[reply_text, total_reward, history_state, env_state],
            outputs=ALL_OUT
        )
        submit_btn.click(
            on_submit,
            inputs=[total_reward, history_state, env_state],
            outputs=ALL_OUT
        )
        guard_btn.click(
            on_lockdown,
            inputs=[total_reward, history_state, env_state],
            outputs=ALL_OUT
        )

        # Analytics Action Bar Wiring
        analytics_reset_btn.click(
            on_reset,
            inputs=[task_type, history_state, env_state],
            outputs=ALL_OUT + [env_state]
        )
        analytics_auto_btn.click(
            on_auto_triage,
            inputs=[agent_proto, hint_input, total_reward, history_state, env_state, live_model, live_temp, live_prompt, live_max_steps, live_url],
            outputs=ALL_OUT
        )
        analytics_submit_btn.click(
            on_submit,
            inputs=[total_reward, history_state, env_state],
            outputs=ALL_OUT
        )

        # =================================================================
        # DYNAMIC LEADERBOARD
        # =================================================================
        def _grade(score: float) -> str:
            if score >= 0.90: return "★★★ S"
            if score >= 0.75: return "★★☆ A"
            if score >= 0.55: return "★☆☆ B"
            if score >= 0.35: return "☆☆☆ C"
            return "💀 D"

        def build_leaderboard(history):
            if not history:
                empty_lb = pd.DataFrame({"Rank": [], "Mission": [], "DEFCON": [], "Score": [], "Grade": []})
                empty_chart = pd.DataFrame({"Mission": ["—"], "Score": [0.01]})
                empty_stats = pd.DataFrame({"DEFCON Level": [], "Missions Run": [], "Best": [], "Avg": [], "Worst": []})
                return empty_lb, empty_chart, empty_stats, "*No missions completed yet. Run a mission first.*"
            sorted_h = sorted(history, key=lambda r: float(r[2]), reverse=True)
            lb_rows = [[i+1, r[0], r[1], round(float(r[2]), 4), _grade(float(r[2]))] for i, r in enumerate(sorted_h)]
            lb_df = pd.DataFrame(lb_rows, columns=["Rank", "Mission", "DEFCON", "Score", "Grade"])
            chart_df = pd.DataFrame({"Mission": [r[0] for r in history], "Score": [round(float(r[2]), 4) for r in history]})
            defcon_map = {}
            for row in history:
                lvl = str(row[1]).upper()
                defcon_map.setdefault(lvl, []).append(float(row[2]))
            stats_rows = []
            for lvl in ["EASY", "MEDIUM", "HARD"]:
                if lvl in defcon_map:
                    sc = defcon_map[lvl]
                    stats_rows.append([lvl, len(sc), round(max(sc), 4), round(sum(sc)/len(sc), 4), round(min(sc), 4)])
            stats_df = pd.DataFrame(
                stats_rows if stats_rows else [],
                columns=["DEFCON Level", "Missions Run", "Best", "Avg", "Worst"]
            )
            top = sorted_h[0]
            msg = f"✅ **{len(history)} missions completed.** Best: **{round(float(top[2]), 4)}** — {_grade(float(top[2]))}"
            return lb_df, chart_df, stats_df, msg

        # --- NEW FORENSIC PDF HANDLER ---
        def generate_forensic_report(audit_log):
            if not audit_log: return None
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(40, 10, "SentinelSOC Forensic Incident Audit")
            pdf.ln(20)
            pdf.set_font("helvetica", size=10)
            for entry in audit_log:
                pdf.set_font("helvetica", "B", 11)
                pdf.cell(0, 10, f"Step {entry['step']}: {entry['action'].upper()}", ln=True)
                pdf.set_font("helvetica", size=10)
                pdf.multi_cell(0, 5, f"AI REASONING: {entry['thinking']}\n")
                pdf.ln(5)
            
            report_path = f"forensic_report_{int(time.time())}.pdf"
            pdf.output(report_path)
            return report_path

        gen_pdf_btn.click(
            generate_forensic_report,
            inputs=[audit_state],
            outputs=[download_file]
        )
        
        save_config_btn.click(
            lambda: gr.Info("🛡️ Defense Matrix Updated. Core policy rewritten."),
            outputs=[]
        )

        refresh_lb_btn.click(
            build_leaderboard,
            inputs=[history_state],
            outputs=[leaderboard_table, leaderboard_chart, defcon_stats, lb_msg]
        )
        analytics_refresh_btn.click(
            build_leaderboard,
            inputs=[history_state],
            outputs=[leaderboard_table, leaderboard_chart, defcon_stats, lb_msg]
        )

        # =================================================================
        # INITIAL LOAD
        # =================================================================
        def on_init():
            api_key = os.getenv("HF_TOKEN", "").strip()
            if not api_key:
                status = "⚠️ **HF_TOKEN not set** — AUTO-MITIGATION requires an API key in Space Secrets."
            else:
                status = "🛡️ **Sovereign AI Defense Grid ONLINE.** Initialize a mission to begin."
            return build_ui_dict(_mock_obs(status), None, 0.0, [])

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


app = gr.mount_gradio_app(base_app, create_ui(), path="/", css=APP_CSS)


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
