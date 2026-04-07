from typing import Literal, Optional
from openenv.core.env_server.types import Action, Observation
from pydantic import Field, ConfigDict

class SentinelAction(Action):
    """Action for the Sentinel SOC environment."""
    action_type: Literal["investigate", "mitigate", "report", "submit", "start_mission"] = Field(
        ..., description="The type of action to perform."
    )
    task_level: Optional[Literal["easy", "medium", "hard"]] = Field(
        None, description="The mission difficulty level (for start_mission)."
    )
    search_query: Optional[str] = Field(
        None, description="The threat intel query (for investigate)."
    )
    reply_text: Optional[str] = Field(
        None, description="The incident report content (for report)."
    )
    team: Optional[Literal["security", "it_support", "billing", "product", "hardware", "hr"]] = Field(
        None, description="The mitigation unit to assign."
    )
    priority: Optional[Literal["low", "medium", "high", "critical", "urgent"]] = Field(
        None, description="The threat severity level."
    )
    status: Optional[Literal["open", "in_progress", "resolved", "escalated"]] = Field(
        "open", description="The cumulative status of the incident."
    )

    model_config = ConfigDict(populate_by_name=True)

class SentinelObservation(Observation):
    """Observation for the Sentinel SOC environment."""
    current_ticket: str = Field(..., description="The current security alert or threat vector.")
    kb_search_results: str = Field(..., description="Retrieved threat intelligence playbooks.")
    ticket_status: str = Field("open", description="Current status of the incident.")
    ticket_priority: str = Field("unassigned", description="Current severity level.")
    ticket_team: str = Field("unassigned", description="Assigned mitigation unit.")
    draft_reply: str = Field("", description="Drafted incident report.")
    system_message: str = Field("", description="Operational telemetry and grader feedback.")
    done: bool = Field(False, description="Whether the mission is complete.")
    reward: float = Field(0.0, description="Cumulative mission efficiency score.")
    step_count: int = Field(0, description="Number of tactical cycles executed.")
