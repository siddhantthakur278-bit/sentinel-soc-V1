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

    def _get_observation(self, system_message: str, done: bool = False, reward: float = 0.0) -> SentinelObservation:
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

    def _compute_potential(self) -> float:
        if not self.task_level or not self._current_task_data:
            return 0.01
        exp = self._current_task_data["expected"]
        score = 0.0
        part_count = 0
        
        # Grading based on correct team routing (incident containment unit)
        if "team" in exp:
            part_count += 1
            if self._ticket_team == exp["team"]:
                score += 1.0
        
        # Grading based on severity assessment
        if "priority" in exp:
            part_count += 1
            if self._ticket_priority == exp["priority"]:
                score += 1.0
        
        # Grading based on incident status lifecycle
        if "status" in exp:
            part_count += 1
            if self._ticket_status == exp["status"]:
                score += 1.0
        
        # Grading based on Incident Report quality
        if "reply_keywords" in exp:
            part_count += 1
            report = self._draft_reply.lower()
            keywords = exp["reply_keywords"]
            if keywords and self._draft_reply.strip():
                matched = sum(1 for kw in keywords if kw in report)
                keyword_score = matched / len(keywords)
                # Bonus for report detail length
                length_bonus = min(len(self._draft_reply) / 600.0, 0.1)
                score += min(keyword_score + length_bonus, 1.0)
                
        # Grading based on Investigative depth (KB Intel)
        if exp.get("requires_kb"):
            part_count += 1
            if self._has_searched_kb:
                kb_score = 0.5
                hint = exp.get("kb_query_hint", "")
                if hint:
                    hint_words = set(hint.lower().split())
                    for query in self._search_history:
                        query_words = set(query.lower().split())
                        if hint_words & query_words:
                            kb_score = 1.0
                            break
                score += kb_score
        
        raw_score = score / part_count if part_count > 0 else 0.0
        return 0.01 + 0.98 * raw_score

    def step(self, action: SentinelAction) -> SentinelObservation:
        self._state.step_count += 1
        system_message = ""
        done = False
        
        if self._state.step_count >= MAX_STEPS:
            done = True
            system_message = "MAX OPERATIONS REACHED. Finalizing incident report."

        if not done:
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
                    query = action.search_query.lower() if action.search_query else ""
                    stop_words = {"how", "do", "i", "the", "to", "at", "on", "was"}
                    q_words = [w.strip("?!.,").lower() for w in query.split() if w.lower() not in stop_words]
                    
                    if not q_words:
                        q_words = [query]

                    results = []
                    for article in KB_ARTICLES:
                        score = 0
                        text = (article["title"] + " " + article["content"] + " " + " ".join(article["tags"])).lower()
                        if query in text: score += 5
                        for word in q_words:
                            if word in text: score += 2
                        if score > 0:
                            results.append((score, article))
                    
                    if results:
                        results.sort(key=lambda x: x[0], reverse=True)
                        top = results[:2]
                        self._kb_search_results = "INTEL RETRIEVED:\n" + "\n".join(
                            [f"[{r[1]['title']}]: {r[1]['content']}" for r in top]
                        )
                        self._has_searched_kb = True
                        self._search_history.append(query)
                        system_message = "Threat intelligence retrieved successfully."
                    else:
                        self._kb_search_results = f"No threat patterns found for '{query}'"
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

        current_score = self._compute_potential()
        step_epsilon = 0.005
        if done:
            cumulative_before = (self._state.step_count - 1) * step_epsilon
            reward = max(current_score - cumulative_before, step_epsilon)
            final_total = cumulative_before + reward
            system_message = f"Task submitted. Final score: {final_total:.2f}/1.00"
        else:
            reward = step_epsilon

        return self._get_observation(system_message, done=done, reward=reward)

    @property
    def state(self) -> State:
        return self._state
