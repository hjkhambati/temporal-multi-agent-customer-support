import asyncio
from workflows.ticket_workflow import TicketWorkflow
from temporalio.client import Client
from data.ticket_models import WorkflowPayload
import os
from dotenv import load_dotenv
load_dotenv()

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")

async def main():
    # Create client connected to server at the given address
    client = await Client.connect(TEMPORAL_ADDRESS)

    # Execute a workflow with more comprehensive test data
    handle = await client.start_workflow(
        TicketWorkflow.run,
        WorkflowPayload(
            ticket_id="ticket-123",
            customer_id="customer-456",
            initial_message="Hi, I ordered wireless headphones last week but they're not working properly. The bluetooth keeps disconnecting and I can't get them to pair with my phone. Can you help me with this?",
            customer_profile={
                "name": "John Doe", 
                "email": "john.doe@example.com",
                "tier": "Gold",
                "phone": "+1-555-0123"
            }
        ),
        id="multi-agent-workflow-test",
        task_queue="customer-support-task-queue",
    )

    print(f"Started workflow. Workflow ID: {handle.id}, RunID {handle.result_run_id}")
    print("You can now interact with this ticket through signals or check its state through queries.")

    # Optionally wait for result (comment out if you want to run async)
    # result = await handle.result()
    # print(result)

if __name__ == "__main__":
    asyncio.run(main())

