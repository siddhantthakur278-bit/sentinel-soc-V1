from typing import Dict
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from models import SentinelAction, SentinelObservation
except ImportError:
    from .models import SentinelAction, SentinelObservation

class SentinelEnv(
    EnvClient[SentinelAction, SentinelObservation, State]
):
    """
    Client for the SentinelSOC Environment.
    """
    def _step_payload(self, action: SentinelAction) -> Dict:
        """Convert SentinelAction to JSON payload."""
        payload = {
            "action_type": action.action_type,
        }
        if action.task_level is not None:
            payload["task_level"] = action.task_level
        if action.search_query is not None:
            payload["search_query"] = action.search_query
        if action.priority is not None:
            payload["priority"] = action.priority
        if action.team is not None:
            payload["team"] = action.team
        if action.status is not None:
            payload["status"] = action.status
        if action.reply_text is not None:
            payload["reply_text"] = action.reply_text
        return payload

    def _parse_result(self, payload: Dict) -> StepResult[SentinelObservation]:
        """Parse server response into StepResult."""
        obs_data = payload.get("observation", {})
        observation = SentinelObservation(
            current_ticket=obs_data.get("current_ticket", ""),
            kb_search_results=obs_data.get("kb_search_results", ""),
            ticket_status=obs_data.get("ticket_status", "open"),
            ticket_priority=obs_data.get("ticket_priority", "unassigned"),
            ticket_team=obs_data.get("ticket_team", "unassigned"),
            draft_reply=obs_data.get("draft_reply", ""),
            system_message=obs_data.get("system_message", ""),
            done=obs_data.get("done", False),
            reward=obs_data.get("reward", 0.0),
            step_count=obs_data.get("step_count", 0),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """Parse server response into State object."""
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
