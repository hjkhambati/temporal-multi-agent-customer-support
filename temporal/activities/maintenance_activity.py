from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from dotenv import load_dotenv
from temporalio import activity
from temporalio.client import Client

from data.base_models import MessageType, TicketStatus
from data.ticket_models import ChatMessage, TicketState

load_dotenv()

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
AUTO_CLOSE_DEFAULT_MINUTES = int(os.getenv("AUTO_CLOSE_INACTIVITY_MINUTES", "60"))
DEFAULT_CLOSURE_MESSAGE = "This ticket is now closed due to inactivity"


def _coerce_utc(dt: datetime | str | None) -> datetime | None:
    if dt is None:
        return None

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


@activity.defn
async def auto_close_inactive_tickets_activity(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Close open tickets that have not been updated within the inactivity window.

    Args:
        config: Optional overrides containing ``inactivity_minutes`` and ``closure_message``.

    Returns:
        Summary statistics including which tickets were closed and any errors encountered.
    """

    config = config or {}
    inactivity_minutes = int(config.get("inactivity_minutes", AUTO_CLOSE_DEFAULT_MINUTES))
    closure_message = config.get("closure_message", DEFAULT_CLOSURE_MESSAGE)

    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=inactivity_minutes)
    closed_tickets: List[str] = []
    evaluated_tickets: List[str] = []

    client = await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)
    
    query = "WorkflowType='TicketWorkflow' AND ExecutionStatus='Running'"
    async for wf in client.list_workflows(query):
        evaluated_tickets.append(wf.id)
        handle = client.get_workflow_handle(wf.id, run_id=wf.run_id)

        state = await handle.query("getState")

        if not state:
            continue

        if isinstance(state, TicketState):
            ticket_state = state
        elif isinstance(state, dict):
            ticket_state = TicketState.from_dict(state)
        else:
            raise TypeError(f"Unexpected state type: {type(state)!r}")

        if ticket_state.status != TicketStatus.OPEN:
            continue

        activity_candidates: List[datetime] = []
        activity_candidates.append(_coerce_utc(ticket_state.last_updated))
        for message in ticket_state.chat_history:
            activity_candidates.append(_coerce_utc(message.timestamp))

        # Filter out any None values that may arise from malformed history
        meaningful_candidates = [dt for dt in activity_candidates if dt is not None]

        last_activity_at = max(meaningful_candidates)
        print(last_activity_at, cutoff_time, wf.id)
        if last_activity_at >= cutoff_time:
            continue

        timestamp_now = datetime.now(timezone.utc)
        message = ChatMessage(
            id=f"auto-close-{uuid.uuid4()}",
            ticket_id=ticket_state.ticket_id or wf.id,
            content=closure_message,
            message_type=MessageType.SYSTEM,
            agent_type=None,
            timestamp=timestamp_now,
            metadata={
                "source": "ticket_auto_close_schedule",
                "closed_at": timestamp_now.isoformat(),
            },
        )

        await handle.signal("addMessage", message.to_dict())
        await handle.signal("updateTicketStatus", TicketStatus.CLOSED.value)
        closed_tickets.append(message.ticket_id)

    return {
        "evaluated": len(evaluated_tickets),
        "closed": len(closed_tickets),
        "closed_ticket_ids": closed_tickets,
        "inactivity_minutes": inactivity_minutes,
    }
