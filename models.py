from typing import Literal, Optional
from openenv.core.env_server.types import Action, Observation
from pydantic import Field
class SupportTicketTriageAction(Action):
    """Action for the Support Ticket Triage environment."""
    action_type: Literal["search_kb", "update_ticket", "reply", "submit", "start_task"] = Field(
        ..., description="The type of action to perform. MUST be one of: search_kb, update_ticket, reply, submit, start_task"
    )
    task_level: Optional[Literal["easy", "medium", "hard"]] = Field(
        None, description="Only for start_task. Selects the difficulty. Values: easy, medium, hard"
    )
    search_query: Optional[str] = Field(None, description="Only for search_kb. The query to search the knowledge base.")
    priority: Optional[Literal["low", "medium", "high", "critical"]] = Field(None, description="Only for update_ticket. Set ticket priority.")
    team: Optional[Literal["billing", "it_support", "product", "hardware"]] = Field(None, description="Only for update_ticket. Assign to a team.")
    status: Optional[Literal["open", "in_progress", "resolved"]] = Field(None, description="Only for update_ticket. Set ticket status.")
    reply_text: Optional[str] = Field(None, description="Only for reply. The text message to the customer.")
class SupportTicketTriageObservation(Observation):
    """Observation from the Support Ticket Triage environment."""
    current_ticket: str = Field(default="", description="The content of the current support ticket.")
    kb_search_results: str = Field(default="", description="Results from the last knowledge base search.")
    ticket_status: str = Field(default="open", description="Current status of the ticket.")
    ticket_priority: str = Field(default="unassigned", description="Current priority of the ticket.")
    ticket_team: str = Field(default="unassigned", description="Currently assigned team.")
    draft_reply: str = Field(default="", description="The current drafted reply to the customer.")
    system_message: str = Field(default="", description="Feedback or error messages from the system.")
    reward: float = Field(default=0.0, description="The reward obtained in the last step.")
    done: bool = Field(default=False, description="Whether the episode is finished.")
    step_count: int = Field(default=0, description="Current step count in the episode.")
