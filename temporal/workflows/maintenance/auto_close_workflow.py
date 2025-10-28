"""Workflow that triggers maintenance activities like auto-closing inactive tickets."""

from datetime import timedelta
from temporalio import workflow

DEFAULT_INACTIVITY_MINUTES = 60
DEFAULT_CLOSURE_MESSAGE = "This ticket is now closed due to inactivity"

with workflow.unsafe.imports_passed_through():
    from typing import Dict, Any
    from activities.maintenance_activity import auto_close_inactive_tickets_activity


@workflow.defn
class TicketAutoCloseWorkflow:
    """Periodic workflow that closes inactive tickets via maintenance activity."""

    @workflow.run
    async def run(self, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        config = config or {}
        inactivity_minutes = int(config.get("inactivity_minutes", DEFAULT_INACTIVITY_MINUTES))
        closure_message = config.get("closure_message", DEFAULT_CLOSURE_MESSAGE)

        activity_payload = {
            "inactivity_minutes": inactivity_minutes,
            "closure_message": closure_message,
        }

        result = await workflow.execute_activity(
            auto_close_inactive_tickets_activity,
            activity_payload,
            start_to_close_timeout=timedelta(minutes=5),
            schedule_to_close_timeout=timedelta(minutes=5),
        )

        return result
