"""Utility script to create or update the ticket auto-close schedule."""

import asyncio
import os
from datetime import timedelta

from dotenv import load_dotenv
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleSpec,
    ScheduleState,
    ScheduleUpdate,
)

from workflows.maintenance.auto_close_workflow import TicketAutoCloseWorkflow

load_dotenv()

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TASK_QUEUE = os.getenv("TASK_QUEUE", "multi-agent-support")
SCHEDULE_ID = os.getenv("AUTO_CLOSE_SCHEDULE_ID", "ticket-auto-close-schedule")


async def ensure_schedule() -> None:
    schedule = Schedule(
        action=ScheduleActionStartWorkflow(
            TicketAutoCloseWorkflow.run,
            id="ticket-auto-close-workflow",
            task_queue=TASK_QUEUE,
            args=[
                {
                    "inactivity_minutes": int(
                        os.getenv("AUTO_CLOSE_INACTIVITY_MINUTES", "10")
                    ),
                    "closure_message": os.getenv(
                        "AUTO_CLOSE_MESSAGE", "This ticket is now closed due to inactivity"
                    ),
                }
            ],
        ),
        spec=ScheduleSpec(
            intervals=[ScheduleIntervalSpec(every=timedelta(minutes=2))],
        ),
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
        state=ScheduleState(note="Auto-closes inactive tickets every 2 minutes"),
    )

    client = await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)
    handle = client.get_schedule_handle(SCHEDULE_ID)

    try:
        await handle.describe()
    except Exception:
        await client.create_schedule(SCHEDULE_ID, schedule)
        print(f"Created schedule '{SCHEDULE_ID}'")
    else:
        await handle.update(lambda _: ScheduleUpdate(schedule=schedule))
        print(f"Updated schedule '{SCHEDULE_ID}'")


if __name__ == "__main__":
    asyncio.run(ensure_schedule())
