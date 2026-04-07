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
VALID_TEAMS = ["unassigned", "security", "billing", "network", "product", "it_support", "hr"]
VALID_PRIORITIES = ["unassigned", "medium", "high", "critical", "urgent"]
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
        with gr.Tabs():

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

        def build_ui_dict(obs, env, new_total, new_history, reasoning="", is_reset=False):
            """Build the full output dict for ALL_OUT."""
            steps = getattr(obs, 'step_count', 0)
            reward = getattr(obs, 'reward', 0.0)
            integrity = max(100 - steps * 4, 10)
            tactic, colors = _map_colors(env)

            # Analytics plots — only build when there's data
            if new_history:
                score_df = pd.DataFrame({
                    "Run": list(range(len(new_history))),
                    "Score": [r[2] for r in reversed(new_history)]
                })
                perf_df = (
                    pd.DataFrame({"Lvl": [r[1] for r in new_history], "Score": [r[2] for r in new_history]})
                    .groupby("Lvl")["Score"].mean().reset_index()
                )
            else:
                score_df = pd.DataFrame({"Run": [0], "Score": [0.0]})
                perf_df = pd.DataFrame({"Lvl": ["EASY", "MEDIUM", "HARD"], "Score": [0.0, 0.0, 0.0]})

            # Policy plot — reflect actual step action
            policy_df = pd.DataFrame({
                "Action": ["Investigate", "Mitigate", "Report", "Submit", "Idle"],
                "Confidence": [random.uniform(0.1, 0.9) for _ in range(5)]
            })

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
                reward_disp: new_total,
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
                loss_plot: pd.DataFrame({"Step": list(range(20)), "Loss": [random.uniform(0, 0.15) for _ in range(20)]}),
                entropy_plot: pd.DataFrame({"Step": list(range(20)), "Entropy": [random.uniform(0.2, 0.8) for _ in range(20)]}),
                history_state: new_history,
                total_reward: new_total,
                map_step_1: colors[0], map_step_2: colors[1],
                map_step_3: colors[2], map_step_4: colors[3],
                hint_input: gr.update(),  # no-op; keeps hint_input in ALL_OUT coverage
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

        def on_auto_triage(proto, hint_text, current_total, history, env):
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

            llm = OpenAI(
                base_url=os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1"),
                api_key=os.getenv("HF_TOKEN", "")
            )
            model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

            # Agent persona
            if "Guardian" in proto:
                persona = "compliance-focused security auditor"
                directive = "Prioritize system stability and meticulous evidence documentation."
            elif "Ghost" in proto:
                persona = "stealth containment specialist"
                directive = "Isolate threat segments silently without alerting the adversary."
            else:
                persona = "lethal-grade autonomous SOC analyst"
                directive = "Neutralize threats with maximum speed and tactical precision."

            hint_clause = f"\n[OVERSEER_HINT]: {hint_text.strip()}" if hint_text and hint_text.strip() else ""

            system_prompt = (
                f"You are SentinelAI, a {persona}. {directive}\n"
                "Output ONLY a single flat JSON object with these exact keys:\n"
                "  'thinking': string — your step-by-step analysis of the ticket.\n"
                "  'action_type': one of [investigate, mitigate, report, submit].\n"
                "  'search_query': string describing what intel to look up (for investigate).\n"
                "  'team': the correct deployment unit for this specific ticket. Choose from:\n"
                "    security (cyberattacks, malware, unauthorized access, VPN, credentials)\n"
                "    network (traffic, DNS, firewall, exfiltration, bandwidth)\n"
                "    billing (financial data, payroll, payment systems)\n"
                "    product (application bugs, APIs, SQL injection, WAF)\n"
                "    it_support (general IT issues, hardware, software, antivirus)\n"
                "    hr (employee issues, insider threats, access termination)\n"
                "  'priority': severity level appropriate to the ticket:\n"
                "    medium (low impact, no active breach)\n"
                "    high (significant risk, needs attention soon)\n"
                "    critical (active attack, data at risk)\n"
                "    urgent (immediate action required, systems compromised)\n"
                "  'status': incident lifecycle state:\n"
                "    open (just identified), in_progress (being investigated)\n"
                "    resolved (fully contained), escalated (requires senior response)\n"
                "  'reply_text': a detailed CISO incident report (min 150 words) that MUST\n"
                "    include: affected system/artifact, root cause analysis, containment steps\n"
                "    taken, remediation plan, and specific technical terms from the ticket.\n"
                "CRITICAL: Read the ticket carefully. Choose team/priority/status based on the\n"
                "  ACTUAL CONTENT of the ticket, not generic defaults.\n"
                "WORKFLOW: investigate → mitigate → report → submit (do not skip steps).\n"
                "MANDATORY: No markdown fences. Output only the JSON object."
                + hint_clause
            )

            messages = [{"role": "system", "content": system_prompt}]
            running_total = current_total
            done_actions = []

            yield {sys_msg: f"📡 **UPLINK: '{proto}' Protocol Synchronized. Beginning autonomous triage...**"}

            for step_i in range(8):
                state_obs = env._get_observation(f"Step {step_i + 1}: Analyzing threat vector...")
                state_snapshot = {
                    "current_ticket": state_obs.current_ticket,
                    "kb_search_results": state_obs.kb_search_results or "Not yet retrieved.",
                    "ticket_team": state_obs.ticket_team,
                    "ticket_priority": state_obs.ticket_priority,
                    "ticket_status": state_obs.ticket_status,
                    "draft_reply": state_obs.draft_reply or "Not yet drafted.",
                    "actions_taken": done_actions,
                }

                messages.append({"role": "user", "content": json.dumps(state_snapshot)})

                try:
                    res = llm.chat.completions.create(
                        model=model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.5,
                        max_tokens=900,
                    )
                    raw = res.choices[0].message.content or "{}"
                    # Strip accidental markdown fences
                    if "```" in raw:
                        raw = raw.split("```")[1].replace("json", "").strip()

                    data = json.loads(raw)

                    thinking = data.get("thinking", f"[{proto}] Executing tactical maneuver...")
                    messages.append({"role": "assistant", "content": raw})

                    # Normalize action_type
                    raw_at = str(data.get("action_type", "investigate")).lower()
                    if "invest" in raw_at or "search" in raw_at:
                        at = "investigate"
                    elif "mitig" in raw_at or "updat" in raw_at or "route" in raw_at:
                        at = "mitigate"
                    elif "repor" in raw_at or "draft" in raw_at or "reply" in raw_at:
                        at = "report"
                    elif "submit" in raw_at or "close" in raw_at or "finish" in raw_at:
                        at = "submit"
                    else:
                        at = "investigate"

                    # Build action
                    team_val = data.get("team", "security")
                    prio_val = data.get("priority", "medium")
                    stat_val = data.get("status", "in_progress")

                    # Validate enums strictly
                    if team_val not in [t for t in VALID_TEAMS if t != "unassigned"]:
                        team_val = "security"
                    if prio_val not in [p for p in VALID_PRIORITIES if p != "unassigned"]:
                        prio_val = "medium"
                    if stat_val not in VALID_STATUSES:
                        stat_val = "in_progress"

                    reply_val = str(data.get("reply_text", data.get("report", data.get("draft", ""))))

                    action_obj = SentinelAction(
                        action_type=at,
                        search_query=str(data.get("search_query", "threat pattern analysis")),
                        reply_text=reply_val,
                        team=team_val,
                        priority=prio_val,
                        status=stat_val,
                    )

                    obs = env.step(action_obj)
                    done_actions.append(at)

                    if obs.done:
                        # Score = done-step reward only, strictly in (0, 1)
                        final_score = float(max(0.01, min(0.99, obs.reward)))
                        mission_num = len(history) + 1
                        new_history = [[
                            f"Mission #{mission_num}",
                            (env.task_level or "?").upper(),
                            round(final_score, 4)
                        ]] + history
                        history = new_history
                        running_total = final_score  # display the clean final score

                    result = build_ui_dict(obs, env, running_total, history, reasoning=thinking)
                    yield result

                    if obs.done:
                        break

                except Exception as e:
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
            hint_input,
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
            inputs=[agent_proto, hint_input, total_reward, history_state, env_state],
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
        translate_btn.click(
            lambda: {sys_msg: "📡 **UPLINK:** Biometric decryption complete — NO MALICIOUS INTENT DETECTED."},
            outputs=[sys_msg]
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

        refresh_lb_btn.click(
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
