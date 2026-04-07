import json
import os
import random
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
try:
    from ..models import SupportTicketTriageAction, SupportTicketTriageObservation
except ImportError:
    from models import SupportTicketTriageAction, SupportTicketTriageObservation
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "tickets.json"), "r") as f:
    ALL_TICKETS = json.load(f)
with open(os.path.join(BASE_DIR, "kb.json"), "r") as f:
    KB_ARTICLES = json.load(f)
MAX_STEPS = 10
STEP_PENALTY = -0.01
class SupportTicketTriageEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS: bool = True
    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.reset_environment_state()
    def reset_environment_state(self):
        self.task_level = None
        self._current_task_data = None
        self._current_ticket = "Welcome to Support Ticket Triage. Please send a 'start_task' action with task_level 'easy', 'medium', or 'hard'."
        self._kb_search_results = ""
        self._ticket_status = "open"
        self._ticket_priority = "unassigned"
        self._ticket_team = "unassigned"
        self._draft_reply = ""
        self._has_searched_kb = False
        self._search_history: list = []  # tracks all queries submitted by the agent
    def reset(self) -> SupportTicketTriageObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.reset_environment_state()
        return self._get_observation("Environment reset.")
    def _get_observation(self, system_message: str, done: bool = False, reward: float = 0.0) -> SupportTicketTriageObservation:
        return SupportTicketTriageObservation(
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
        if "team" in exp:
            part_count += 1
            if self._ticket_team == exp["team"]:
                score += 1.0
        if "priority" in exp:
            part_count += 1
            if self._ticket_priority == exp["priority"]:
                score += 1.0
        if "status" in exp:
            part_count += 1
            if self._ticket_status == exp["status"]:
                score += 1.0
        if "reply_keywords" in exp:
            part_count += 1
            reply = self._draft_reply.lower()
            keywords = exp["reply_keywords"]
            if keywords and self._draft_reply.strip():
                # Fuzzy: partial credit based on fraction of keywords matched
                matched = sum(1 for kw in keywords if kw in reply)
                keyword_score = matched / len(keywords)
                # Bonus: reward longer, more detailed replies (up to 0.15 bonus)
                length_bonus = min(len(self._draft_reply) / 800.0, 0.15)
                score += min(keyword_score + length_bonus, 1.0)
        if exp.get("requires_kb"):
            part_count += 1
            if self._has_searched_kb:
                # Base score for searching at all
                kb_score = 0.5
                # Bonus if any search query semantically overlaps with the expected hint
                hint = exp.get("kb_query_hint", "")
                if hint:
                    hint_words = set(hint.lower().split())
                    for query in self._search_history:
                        query_words = set(query.lower().split())
                        if hint_words & query_words:  # non-empty intersection
                            kb_score = 1.0
                            break
                score += kb_score
        raw_score = score / part_count if part_count > 0 else 0.0
        # Map [0, 1] to [0.01, 0.99] to be strictly within (0, 1)
        return 0.01 + 0.98 * raw_score
    def step(self, action: SupportTicketTriageAction) -> SupportTicketTriageObservation:  # type: ignore[override]
        self._state.step_count += 1
        prev_potential = self._compute_potential()
        system_message = ""
        reward_penalty = STEP_PENALTY
        done = False
        if self._state.step_count >= MAX_STEPS:
            done = True
            system_message = "Max steps reached. Finalizing task."
        if not done:
            if action.action_type == "start_task":
                if action.task_level not in ALL_TICKETS:
                    system_message = "Invalid task_level. Must be easy, medium, or hard."
                    reward_penalty -= 0.1
                else:
                    self.task_level = action.task_level
                    self._current_task_data = random.choice(ALL_TICKETS[self.task_level])
                    self._current_ticket = self._current_task_data["ticket"]
                    self._kb_search_results = ""
                    self._ticket_status = "open"
                    self._ticket_priority = "unassigned"
                    self._ticket_team = "unassigned"
                    self._draft_reply = ""
                    self._has_searched_kb = False
                    self._search_history = []
                    system_message = f"Started task: {self.task_level}"
                    prev_potential = self._compute_potential()
            elif action.action_type == "search_kb":
                if not self.task_level:
                    system_message = "Must start task first."
                    reward_penalty -= 0.1
                else:
                    # High-precision search logic
                    query = action.search_query.lower()
                    stop_words = {"how", "do", "i", "my", "is", "a", "the", "to", "can", "help", "please", "me", "what", "with", "for", "am", "are"}
                    q_words = [w.strip("?!.,").lower() for w in query.split() if w.strip("?!.,").lower() not in stop_words]
                    
                    if not q_words:
                        q_words = [w.lower() for w in query.split()]

                    results = []
                    for article in KB_ARTICLES:
                        score = 0
                        text = (article["title"] + " " + article["content"] + " " + " ".join(article["tags"])).lower()
                        if query in text:
                            score += 5  # High boost for exact query substring
                        for word in q_words:
                            if word in text:
                                score += 2  # Boost for exact word match
                        if score > 0:
                            results.append((score, article))
                    
                    if results:
                        results.sort(key=lambda x: x[0], reverse=True)
                        top_results = results[:2]
                        self._kb_search_results = "FOUND:\n" + "\n".join(
                            [f"- {r[1]['title']}: {r[1]['content']}" for r in top_results]
                        )
                        self._has_searched_kb = True
                        self._search_history.append(query)  # track query for quality grading
                        system_message = "Found knowledge base article(s)."
                    else:
                        self._kb_search_results = f"No results for '{query}'"
                        system_message = "No relevant articles found."
                        reward_penalty -= 0.05
            elif action.action_type == "update_ticket":
                if not self.task_level:
                    system_message = "Must start task first."
                    reward_penalty -= 0.1
                else:
                    updates = []
                    if action.priority:
                        self._ticket_priority = action.priority
                        updates.append(f"priority={action.priority}")
                    if action.team:
                        self._ticket_team = action.team
                        updates.append(f"team={action.team}")
                        # Provide routing quality hint for helpful RL signal
                        ticket_lower = self._current_ticket.lower()
                        billing_kw = any(k in ticket_lower for k in ["refund", "charge", "billing", "payment", "invoice"])
                        security_kw = any(k in ticket_lower for k in ["phishing", "ransomware", "breach", "firewall"])
                        hr_kw = any(k in ticket_lower for k in ["payroll", "paycheck", "hire", "onboarding", "activedirectory"])
                        if billing_kw and action.team != "billing":
                            system_message = f"Routing hint: billing-related keywords detected."
                        elif security_kw and action.team != "security":
                            system_message = f"Routing hint: security incident keywords detected."
                        elif hr_kw and action.team not in ["hr", "it_support"]:
                            system_message = f"Routing hint: HR-related keywords detected."
                    if action.status:
                        self._ticket_status = action.status
                        updates.append(f"status={action.status}")
                    if updates:
                        if not system_message:
                            system_message = f"Ticket updated: {', '.join(updates)}"
                    else:
                        system_message = "No fields provided to update."
                        reward_penalty -= 0.05
            elif action.action_type == "reply":
                if not self.task_level:
                    system_message = "Must start task first."
                    reward_penalty -= 0.1
                elif not action.reply_text:
                    system_message = "reply_text is required for reply action."
                    reward_penalty -= 0.1
                else:
                    self._draft_reply = action.reply_text
                    system_message = "Draft reply updated."
            elif action.action_type == "submit":
                if not self.task_level:
                    system_message = "Must start task first."
                    reward_penalty -= 0.1
                else:
                    done = True
                    score = self._compute_potential()
                    # Strictly between 0 and 1 (0.01 to 0.99)
                    score = min(max(score, 0.01), 0.99)
                    system_message = f"Task submitted. Final score: {score:.2f}/1.00"
            else:
                system_message = f"Unknown action type: {action.action_type}"
                reward_penalty -= 0.1
        current_potential = self._compute_potential()
        reward = (current_potential - prev_potential) + reward_penalty
        return self._get_observation(system_message, done=done, reward=reward)
    @property
    def state(self) -> State:
        return self._state
