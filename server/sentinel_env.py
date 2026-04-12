import json
import os
import random
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
try:
    from models import SentinelAction, SentinelObservation
except ImportError:
    from ..models import SentinelAction, SentinelObservation

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "tickets.json"), "r") as f:
    ALL_TICKETS = json.load(f)
with open(os.path.join(BASE_DIR, "kb.json"), "r") as f:
    KB_ARTICLES = json.load(f)

MAX_STEPS = 10

class SentinelSOCEnvironment(Environment):
    """
    SentinelSOC: Autonomous Security Operations Center Environment.
    An agentic environment for triage and mitigation of cyber-security incidents.
    """
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.reset_environment_state()

    def reset_environment_state(self):
        self.task_level = None
        self._current_task_data = None
        self._current_ticket = "Welcome to SentinelSOC Command Center. Awaiting mission parameters. Send 'start_mission' with level 'easy', 'medium', or 'hard'."
        self._kb_search_results = ""
        self._ticket_status = "open"
        self._ticket_priority = "unassigned"
        self._ticket_team = "unassigned"
        self._draft_reply = ""
        self._has_searched_kb = False
        self._search_history: list = []  # tracks all queries submitted by the agent

    def reset(self) -> SentinelObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.reset_environment_state()
        return self._get_observation("SOC Terminal Initialized. Ready for intake.")

    def _get_observation(self, system_message: str, done: bool = False, reward: float = 0.01) -> SentinelObservation:
        return SentinelObservation(
            current_ticket=self._current_ticket,
            kb_search_results=self._kb_search_results,
            ticket_status=self._ticket_status,
            ticket_priority=self._ticket_priority,
            ticket_team=self._ticket_team,
            draft_reply=self._draft_reply,
            system_message=system_message,
            done=done,
            reward=reward,
            step_count=self._state.step_count,
        )

    # Ordinal scales for partial-credit scoring
    PRIORITY_SCALE = {"medium": 1, "high": 2, "critical": 3, "urgent": 4}
    STATUS_SCALE   = {"open": 0, "in_progress": 1, "resolved": 2, "escalated": 3}

    def _compute_potential(self) -> float:
        if not self.task_level or not self._current_task_data:
            return 0.01
        exp = self._current_task_data["expected"]
        score = 0.0
        part_count = 0

        # ── Team routing: binary (either you routed correctly or not) ──────
        if "team" in exp:
            part_count += 1
            if self._ticket_team == exp["team"]:
                score += 1.0
            # Partial credit if team is unassigned (agent didn't try at all)
            elif self._ticket_team not in ("unassigned", None):
                score += 0.2  # tried but wrong team

        # ── Priority: ordinal partial credit ────────────────────────────────
        if "priority" in exp:
            part_count += 1
            exp_p = self.PRIORITY_SCALE.get(exp["priority"], 0)
            got_p = self.PRIORITY_SCALE.get(self._ticket_priority, 0)
            if exp_p == got_p:
                score += 1.0
            elif got_p > 0:  # at least assigned something
                diff = abs(exp_p - got_p)
                score += max(0.0, 1.0 - diff * 0.4)  # -0.4 per level off

        # ── Status: ordinal partial credit ───────────────────────────────────
        if "status" in exp:
            part_count += 1
            exp_s = self.STATUS_SCALE.get(exp["status"], 0)
            got_s = self.STATUS_SCALE.get(self._ticket_status, 0)
            if exp_s == got_s:
                score += 1.0
            else:
                diff = abs(exp_s - got_s)
                score += max(0.0, 1.0 - diff * 0.35)  # -0.35 per step off

        # ── Incident report quality: keyword coverage + length ────────────────
        if "reply_keywords" in exp:
            part_count += 1
            report = self._draft_reply.lower()
            keywords = exp["reply_keywords"]
            if keywords and self._draft_reply.strip():
                matched = sum(1 for kw in keywords if kw in report)
                keyword_score = matched / len(keywords)
                # Bonus for detailed report (up to +0.15)
                length_bonus = min(len(self._draft_reply) / 500.0, 0.15)
                score += min(keyword_score + length_bonus, 1.0)
            # Empty report → 0 added

        # ── KB investigation depth ────────────────────────────────────────────
        if exp.get("requires_kb"):
            part_count += 1
            if self._has_searched_kb:
                kb_score = 0.4  # base: searched something
                hint = exp.get("kb_query_hint", "")
                if hint:
                    hint_words = set(hint.lower().split())
                    best = 0.0
                    for query in self._search_history:
                        q_words = set(query.lower().split())
                        overlap = len(hint_words & q_words) / max(len(hint_words), 1)
                        best = max(best, overlap)
                    # Scale from 0.4 (no overlap) to 1.0 (perfect overlap)
                    kb_score = 0.4 + 0.6 * best
                score += kb_score

        raw_score = score / part_count if part_count > 0 else 0.0
        # Strictly between 0 and 1: clamp to [0.01, 0.99]
        return max(0.01, min(0.99, raw_score))

    def step(self, action: SentinelAction) -> SentinelObservation:
        self._state.step_count += 1
        system_message = ""
        done = False
        
        if self._state.step_count >= MAX_STEPS:
            done = True
            system_message = "MAX OPERATIONS REACHED. Finalizing incident report."

        if not done:
            # Universal Metadata Synchronization
            if self.task_level and action.action_type not in ["start_mission", "start_task"]:
                if action.priority: self._ticket_priority = action.priority
                if action.team: self._ticket_team = action.team
                if action.status: self._ticket_status = action.status
                if action.reply_text: self._draft_reply = action.reply_text

            # SOC Action: Initiate Investigation / Mission
            if action.action_type in ["start_mission", "start_task"]:
                # support both names for compatibility
                lvl = action.task_level or "easy"
                if lvl not in ALL_TICKETS:
                    system_message = "ERROR: Invalid Mission Level."
                else:
                    self.task_level = lvl
                    self._current_task_data = random.choice(ALL_TICKETS[self.task_level])
                    self._current_ticket = self._current_task_data["ticket"]
                    self._kb_search_results = ""
                    self._ticket_status = "open"
                    self._ticket_priority = "unassigned"
                    self._ticket_team = "unassigned"
                    self._draft_reply = ""
                    self._has_searched_kb = False
                    self._search_history = []
                    system_message = f"ACTIVE ALERT: {self.task_level.upper()} LEVEL THREAT INITIALIZED."

            # SOC Action: Investigate Intelligence / Logs
            elif action.action_type in ["investigate", "search_kb"]:
                if not self.task_level:
                    system_message = "ERROR: Command Bridge not ready. Start mission first."
                else:
                    # Improved Semantic Search (keyword-based ranking with term frequency and importance)
                    import re
                    query = action.search_query.lower() if action.search_query else ""
                    # Remove common security fluff and stop words
                    fluff = {"how", "do", "i", "the", "to", "at", "on", "was", "for", "in", "of", "and", "is", "a", "an", "what", "threat", "intel", "playbook", "search", "patterns"}
                    q_words = [w.strip("?!.,").lower() for w in query.split() if w.lower() not in fluff]
                    
                    if not q_words:
                        q_words = [query] if query else ["logs"]

                    scored_results = []
                    for article in KB_ARTICLES:
                        score = 0
                        title_norm = article["title"].lower()
                        content_norm = article["content"].lower()
                        tags_norm = [t.lower() for t in article["tags"]]
                        
                        # High weight for title matches
                        for word in q_words:
                            if word in title_norm:
                                score += 10
                            if word in content_norm:
                                score += 3
                            if any(word in t for t in tags_norm):
                                score += 5
                        
                        # Bonus for perfect query match in title
                        if query in title_norm:
                            score += 15
                        
                        if score > 0:
                            scored_results.append((score, article))
                    
                    if scored_results:
                        scored_results.sort(key=lambda x: x[0], reverse=True)
                        top = scored_results[:3] # Show top 3 for better coverage
                        self._kb_search_results = "INTEL RETRIEVED:\n" + "\n".join(
                            [f"[{r[1]['title']}]: {r[1]['content']}" for r in top]
                        )
                        self._has_searched_kb = True
                        self._search_history.append(query)
                        system_message = f"Threat intelligence retrieved ({len(scored_results)} matches found)."
                    else:
                        self._kb_search_results = f"No threat patterns found for '{query}'. Try broader terms (e.g. 'phishing', 'ransomware', 'access')."
                        system_message = "Zero matches found in Intelligence Database."

            # SOC Action: Mitigate and Route
            elif action.action_type in ["mitigate", "update_ticket"]:
                if not self.task_level:
                    system_message = "ERROR: Command Bridge not ready."
                else:
                    updates = []
                    if action.priority:
                        self._ticket_priority = action.priority
                        updates.append(f"severity={action.priority}")
                    if action.team:
                        self._ticket_team = action.team
                        updates.append(f"deployment_unit={action.team}")
                    if action.status:
                        self._ticket_status = action.status
                        updates.append(f"incident_status={action.status}")
                    if action.reply_text:
                        self._draft_reply = action.reply_text
                        updates.append("draft_synchronized")
                    
                    if updates:
                        system_message = f"SITUATION REPORT: {', '.join(updates)}"
                    else:
                        system_message = "No mitigation parameters provided."

            # SOC Action: Incident Report Drafting
            elif action.action_type in ["report", "reply"]:
                if not self.task_level:
                    system_message = "ERROR: Command Bridge not ready."
                elif not action.reply_text:
                    system_message = "REPORT FAILURE: Report content cannot be empty."
                else:
                    self._draft_reply = action.reply_text
                    system_message = "Incident Report Draft synchronized."

            # SOC Action: Submit and Close
            elif action.action_type == "submit":
                if not self.task_level:
                    system_message = "ERROR: Command Bridge not ready."
                else:
                    done = True
            
            else:
                system_message = f"UNRECOGNIZED COMMAND: {action.action_type}"

        current_score = self._compute_potential()  # always in [0.01, 0.99]
        # Intermediate steps get a small reward to keep the agent exploring.
        # STEP_EPS must be >= 0.005 so that :.2f formatting gives '0.01', not '0.00'
        STEP_EPS = 0.01
        if done:
            # Final reward IS the quality score — strictly between 0 and 1.
            reward = float(max(0.01, min(0.99, current_score)))
            system_message = f"Task submitted. Final score: {reward:.4f}/1.00"
        else:
            reward = STEP_EPS

        # Universal safety clamp: reward must be strictly in (0, 1) — never 0.0 or 1.0
        # Round to 2 decimal places as requested
        reward = float(max(0.01, min(0.99, round(reward, 2))))

        return self._get_observation(system_message, done=done, reward=reward)

    @property
    def state(self) -> State:
        return self._state
