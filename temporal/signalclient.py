import asyncio
from temporalio.client import Client
import os
from dotenv import load_dotenv
from data.base_models import TicketStatus
from data.ticket_models import ChatMessage
from data.base_models import MessageType, AgentType
from datetime import datetime
load_dotenv()

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")

async def main():
    client = await Client.connect(TEMPORAL_ADDRESS)
    handle = client.get_workflow_handle("multi-agent-workflow-test")
    
    # Example: Add a follow-up customer message
    followup_message = ChatMessage(
        id="msg-followup-001",
        ticket_id="ticket-123",
        content="The troubleshooting steps you provided didn't work. I'm still having the same bluetooth issue. This is really frustrating!",
        message_type=MessageType.CUSTOMER,
        agent_type=None,
        timestamp=datetime.now()
    )
    
    print("Sending follow-up message...")
    # Convert to dict for JSON serialization
    await handle.signal("addMessage", followup_message.to_dict())
    
    # Check current state
    print("Getting current ticket state...")
    current_state_dict = await handle.query("getState")
    if current_state_dict:
        print(f"Current status: {current_state_dict['status']}")
        print(f"Assigned agent: {current_state_dict['assigned_agent_type'] or 'None'}")
        print(f"Chat history length: {len(current_state_dict['chat_history'])}")
    else:
        print("No ticket state found")

if __name__ == "__main__":
    asyncio.run(main())