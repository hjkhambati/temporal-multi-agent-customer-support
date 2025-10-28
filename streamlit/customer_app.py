"""
Improved Customer Support Interface with Proper Polling and Ticket Management
"""
import streamlit as st
import asyncio
import nest_asyncio
import uuid
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from temporalio.client import Client
from temporal.data.base_models import MessageType, AgentType, TicketStatus
from temporal.data.ticket_models import ChatMessage, WorkflowPayload
from temporal.data.persistent_data import get_customers

# Configuration
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TASK_QUEUE = os.getenv("TASK_QUEUE", "multi-agent-support")
AUTO_REFRESH_INTERVAL = "2s"  # Streamlit fragment format (e.g., "2s", "1000ms")

def run_async(coro):
    """Run async function synchronously - Streamlit compatible"""
    nest_asyncio.apply()
    
    try:
        return asyncio.run(coro)
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        else:
            raise


@st.cache_resource
def get_temporal_client():
    """Get cached Temporal client"""
    return run_async(Client.connect(TEMPORAL_ADDRESS))

st.set_page_config(
    page_title="Customer Support Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clean Professional CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.stApp {
    background-color: #f8fafc;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.main .block-container {
    max-width: 1200px;
    padding-top: 2rem;
}

.main-header {
    background: #ffffff;
    color: #1f2937;
    padding: 2rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    text-align: center;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.main-header h1 {
    color: #1f2937;
    font-weight: 700;
    margin: 0;
    font-size: 2rem;
}

.main-header p {
    color: #6b7280;
    margin: 0.5rem 0 0 0;
    font-size: 1rem;
}

.chat-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 1.5rem;
    border-radius: 12px;
    background: #ffffff;
    margin: 1rem 0;
    border: 1px solid #e5e7eb;
}

.chat-container::-webkit-scrollbar {
    width: 8px;
}

.chat-container::-webkit-scrollbar-track {
    background: #f9fafb;
    border-radius: 4px;
}

.chat-container::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 4px;
}

.message-wrapper {
    display: flex;
    margin: 1.25rem 0;
}

.message-wrapper.user {
    justify-content: flex-end;
}

.message-wrapper.agent {
    justify-content: flex-start;
}

.message-wrapper.system {
    justify-content: center;
}

.chat-message {
    max-width: 75%;
    padding: 0.875rem 1.125rem;
    border-radius: 12px;
    line-height: 1.5;
    word-wrap: break-word;
}

.user-message {
    background: #2563eb;
    color: white;
}

.agent-message {
    background: #f3f4f6;
    color: #1f2937;
    border: 1px solid #e5e7eb;
}

.system-message {
    background: #fef3c7;
    color: #92400e;
    text-align: center;
    font-style: italic;
    border-radius: 8px;
    max-width: 80%;
    border: 1px solid #fcd34d;
}

.message-meta {
    font-size: 0.8125rem;
    color: #6b7280;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.user-message .message-meta {
    color: rgba(255, 255, 255, 0.9);
}

.additional-info {
    margin-top: 0.75rem;
    padding: 0.875rem;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 8px;
    border-left: 3px solid #3b82f6;
    font-size: 0.9rem;
}

.status-badge {
    display: inline-block;
    padding: 0.375rem 0.75rem;
    border-radius: 6px;
    font-size: 0.8125rem;
    font-weight: 600;
    text-transform: uppercase;
    margin: 0.25rem;
}

.status-open { 
    background: #dcfce7;
    color: #166534;
}

.status-in-progress { 
    background: #dbeafe;
    color: #1e40af;
}

.status-resolved { 
    background: #f3f4f6;
    color: #374151;
}

.status-escalated-to-human { 
    background: #fee2e2;
    color: #991b1b;
}

.status-closed {
    background: #f3f4f6;
    color: #374151;
}

.ticket-header {
    background: transparent;
    color: #1f2937;
    padding: 1rem 0;
    margin-bottom: 1rem;
    border-bottom: 2px solid #e5e7eb;
}

.ticket-header h3 {
    color: #1f2937;
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
}

.ticket-header p {
    color: #6b7280;
    margin: 0.5rem 0 0 0;
    font-size: 0.9375rem;
}

.info-card {
    background: #ffffff;
    padding: 1.25rem;
    border-radius: 8px;
    margin: 1rem 0;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.stButton > button {
    border-radius: 8px;
    border: none;
    font-weight: 600;
    padding: 0.625rem 1.25rem;
    font-size: 0.9375rem;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.ticket-action-buttons {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Core functions
async def create_new_ticket(customer_id: str, initial_message: str, customer_profile: Dict[str, Any]) -> Optional[str]:
    """Create a new support ticket workflow"""
    try:
        client = get_temporal_client()
        ticket_id = f"ticket-{uuid.uuid4().hex[:8]}"
        
        payload = WorkflowPayload(
            ticket_id=ticket_id,
            customer_id=customer_id,
            initial_message=initial_message,
            customer_profile=customer_profile
        )
        
        await client.start_workflow(
            "TicketWorkflow",
            payload,
            id=ticket_id,
            task_queue=TASK_QUEUE
        )
        
        return ticket_id
    except Exception as e:
        st.error(f"Failed to create ticket: {str(e)}")
        return None

async def send_message_to_ticket(ticket_id: str, message: str, customer_id: str) -> bool:
    """Send a new message to an existing ticket"""
    try:
        client = get_temporal_client()
        handle = client.get_workflow_handle(ticket_id)
        
        chat_message = ChatMessage(
            id=f"msg-{uuid.uuid4().hex[:8]}",
            ticket_id=ticket_id,
            content=message,
            message_type=MessageType.CUSTOMER,
            agent_type=None,
            timestamp=datetime.now()
        )
        
        await handle.signal("addMessage", chat_message.to_dict())
        return True
    except Exception as e:
        st.error(f"Failed to send message: {str(e)}")
        return False

async def get_ticket_state(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Get current state of a ticket"""
    try:
        client = get_temporal_client()
        handle = client.get_workflow_handle(ticket_id)
        state = await handle.query("getState")
        return state
    except Exception as e:
        print(f"Error getting ticket state: {e}")
        return None


async def list_customer_tickets(customer_id: str) -> List[Dict[str, Any]]:
    """Return all active tickets for a customer."""
    client = get_temporal_client()
    tickets: List[Dict[str, Any]] = []

    try:
        async for workflow in client.list_workflows("WorkflowType='TicketWorkflow'"):
            handle = client.get_workflow_handle(workflow.id)
            try:
                state = await handle.query("getState")
            except Exception:
                continue

            if not state:
                continue

            if state.get("customer_id") != customer_id:
                continue

            tickets.append({
                "ticket_id": state.get("ticket_id"),
                "status": state.get("status"),
                "last_updated": state.get("last_updated"),
            })

    except Exception as exc:
        print(f"Error listing customer tickets: {exc}")

    tickets.sort(key=lambda item: item.get("last_updated") or "", reverse=True)
    return tickets

async def close_ticket_by_customer(ticket_id: str, customer_id: str) -> bool:
    """Allow customer to close their own ticket without posting to chat."""
    try:
        client = get_temporal_client()
        handle = client.get_workflow_handle(ticket_id)
        
        await handle.signal("updateTicketStatus", "closed")
        return True
    except Exception as e:
        st.error(f"Failed to close ticket: {str(e)}")
        return False

async def mark_ticket_resolved(ticket_id: str, customer_id: str) -> bool:
    """Allow customer to mark ticket as resolved without adding chat messages."""
    try:
        client = get_temporal_client()
        handle = client.get_workflow_handle(ticket_id)
        
        await handle.signal("updateTicketStatus", "resolved")
        return True
    except Exception as e:
        st.error(f"Failed to resolve ticket: {str(e)}")
        return False

def display_chat_history(chat_history: list, pending_questions: dict, ticket_id: str):
    """Display chat history with enhanced formatting and inline pending questions"""
    if not chat_history:
        st.info("AI agents are analyzing your request...")
        return
    
    for message in chat_history:
        timestamp_str = message.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                time_display = timestamp.strftime("%H:%M")
            except:
                time_display = "Time"
        else:
            time_display = "Time"
        
        content = message.get('content', 'No content')
        message_type = message.get('message_type', 'UNKNOWN')
        agent_type = message.get('agent_type')
        additional_info = message.get('additional_info', {})
        metadata = message.get('metadata', {})
        
        # Check if customer message
        is_customer = (
            message_type == 'CUSTOMER' or 
            message_type == 'customer' or 
            str(message_type) == 'MessageType.CUSTOMER' or 
            (hasattr(message_type, 'value') and message_type.value == 'customer')
        )
        
        if is_customer:
            with st.chat_message("user"):
                st.write(content)
        else:
            agent_name = get_agent_display_name(agent_type)
            with st.chat_message("assistant"):
                st.write(f"**{agent_name}**")
                st.write(content)
                
                # Display additional structured information
                if additional_info:
                    formatted_info = format_additional_info_text(agent_type, additional_info)
                    if formatted_info:
                        st.info(formatted_info)

def get_agent_display_name(agent_type):
    """Get user-friendly agent name"""
    if not agent_type or agent_type == 'SYSTEM':
        return 'AI Assistant'
    
    agent_names = {
        'INTENT_CLASSIFIER': "Intent Analyzer",
        'ORCHESTRATOR': "Orchestrator",
        'ORDER_SPECIALIST': "Order Specialist",
        'TECHNICAL_SPECIALIST': "Technical Support",
        'REFUND_SPECIALIST': "Refund Specialist",
        'GENERAL_SUPPORT': "Support Agent",
        'ESCALATION_MANAGER': "Escalation Manager",
        'MALE_SPECIALIST': "Men's Clothing Specialist",
        'FEMALE_SPECIALIST': "Women's Clothing Specialist",
        'BILLING': "Billing Specialist",
        'DELIVERY': "Delivery Coordinator",
        'ALTERATION': "Alteration Specialist"
    }
    
    return agent_names.get(str(agent_type), f"{str(agent_type).replace('_', ' ').title()}")

def format_json_field(json_str, title, emoji):
    """Parse and format JSON string into readable text"""
    import json
    try:
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        if isinstance(data, dict):
            lines = [f"{emoji} {title}:"]
            for key, value in data.items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, float):
                    lines.append(f"  • {formatted_key}: ${value:.2f}" if 'price' in key.lower() or 'cost' in key.lower() or 'amount' in key.lower() else f"  • {formatted_key}: {value:.2f}")
                else:
                    lines.append(f"  • {formatted_key}: {value}")
            return "\n".join(lines)
        else:
            return f"{emoji} {title}:\n{data}"
    except:
        # If parsing fails, return as-is
        return f"{emoji} {title}:\n{json_str}"

def format_additional_info_text(agent_type, additional_info):
    """Format additional information based on agent type as plain text"""
    if not additional_info:
        return ""
    
    content = []
    agent_type_str = str(agent_type).lower()
    
    # Technical Specialist - actual fields: troubleshooting_steps, estimated_resolution_time
    if 'technical' in agent_type_str:
        if additional_info.get('troubleshooting_steps'):
            content.append(f"🔧 Troubleshooting Steps:\n{additional_info['troubleshooting_steps']}")
        if additional_info.get('estimated_resolution_time'):
            content.append(f"⏱️ Estimated Resolution Time: {additional_info['estimated_resolution_time']}")
    
    # Refund Specialist - actual fields: eligibility_assessment, required_documentation, processing_timeline
    elif 'refund' in agent_type_str:
        if additional_info.get('eligibility_assessment'):
            content.append(f"✅ Eligibility Assessment:\n{additional_info['eligibility_assessment']}")
        if additional_info.get('required_documentation'):
            content.append(f"📄 Required Documentation:\n{additional_info['required_documentation']}")
        if additional_info.get('processing_timeline'):
            content.append(f"⏰ Processing Timeline: {additional_info['processing_timeline']}")
    
    # Order Specialist - actual fields: suggested_actions
    elif 'order' in agent_type_str:
        if additional_info.get('suggested_actions'):
            content.append(f"📋 Suggested Actions:\n{additional_info['suggested_actions']}")
    
    # General Support - actual fields: suggested_actions
    elif 'general' in agent_type_str:
        if additional_info.get('suggested_actions'):
            content.append(f"💡 Suggested Actions:\n{additional_info['suggested_actions']}")
    
    # Male/Female Specialist - actual fields: measurements_collected, measurements_data, validation_status
    elif 'male_specialist' in agent_type_str or 'female_specialist' in agent_type_str:
        if additional_info.get('measurements_collected') is not None:
            content.append(f"📏 Measurements Collected: {'✅ Yes' if additional_info['measurements_collected'] else '❌ No'}")
        if additional_info.get('measurements_data'):
            # Parse JSON measurements data
            content.append(format_json_field(additional_info['measurements_data'], "Measurements", "📐"))
        if additional_info.get('validation_status'):
            content.append(f"✔️ Validation Status: {additional_info['validation_status']}")
    
    # Billing Agent - actual fields: billing_complete, total_amount, payment_status, invoice_details
    elif 'billing' in agent_type_str:
        if additional_info.get('billing_complete') is not None:
            content.append(f"💰 Billing Complete: {'✅ Yes' if additional_info['billing_complete'] else '⏳ Pending'}")
        if additional_info.get('total_amount') is not None:
            content.append(f"💵 Total Amount: ${additional_info['total_amount']:.2f}")
        if additional_info.get('payment_status'):
            content.append(f"💳 Payment Status: {additional_info['payment_status']}")
        if additional_info.get('invoice_details'):
            # Parse JSON invoice details
            content.append(format_json_field(additional_info['invoice_details'], "Invoice Details", "📄"))
    
    # Delivery Agent - actual fields: delivery_scheduled, delivery_date, tracking_number, delivery_address
    elif 'delivery' in agent_type_str:
        if additional_info.get('delivery_scheduled') is not None:
            content.append(f"🚚 Delivery Scheduled: {'✅ Yes' if additional_info['delivery_scheduled'] else '⏳ Pending'}")
        if additional_info.get('delivery_date'):
            content.append(f"📅 Delivery Date: {additional_info['delivery_date']}")
        if additional_info.get('tracking_number'):
            content.append(f"📦 Tracking Number: {additional_info['tracking_number']}")
        if additional_info.get('delivery_address'):
            content.append(f"📍 Delivery Address:\n{additional_info['delivery_address']}")
    
    # Alteration Agent - actual fields: alteration_needed, alteration_details, additional_cost
    elif 'alteration' in agent_type_str:
        if additional_info.get('alteration_needed') is not None:
            content.append(f"✂️ Alteration Needed: {'✅ Yes' if additional_info['alteration_needed'] else '❌ No'}")
        if additional_info.get('alteration_details'):
            content.append(f"✂️ Alteration Details:\n{additional_info['alteration_details']}")
        if additional_info.get('additional_cost') is not None:
            content.append(f"💵 Additional Cost: ${additional_info['additional_cost']:.2f}")
    
    # Orchestrator
    elif 'orchestrator' in agent_type_str:
        if additional_info.get('synthesis_reasoning'):
            content.append(f"🤖 Reasoning:\n{additional_info['synthesis_reasoning']}")
        if additional_info.get('agents_used'):
            content.append(f"👥 Agents Consulted: {', '.join(additional_info['agents_used'])}")
    
    return "\n\n".join(content) if content else ""

def display_ticket_header(ticket_state: Dict[str, Any]):
    """Display enhanced ticket header"""
    status = ticket_state.get('status', 'Unknown')
    ticket_id = ticket_state.get('ticket_id', 'Unknown')
    created_at_str = ticket_state.get('created_at')
    assigned_agent = ticket_state.get('assigned_agent_type', '')
    
    if created_at_str:
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            created_at = created_at.strftime("%Y-%m-%d %H:%M")
        except:
            created_at = "Unknown"
    else:
        created_at = "Unknown"
    
    status_class = f"status-{status.lower().replace('_', '-')}" if status else "status-unknown"
    status_display = status.replace('_', ' ').title() if status else "Unknown"
    
    agent_display = ""
    if assigned_agent:
        agent_display = f" | Assigned to: {get_agent_display_name(assigned_agent)}"
    
    st.markdown(f"""
    <div class="ticket-header">
        <h3>Support Ticket #{ticket_id}</h3>
        <p>
            Created: {created_at}{agent_display}<br>
            <span class="status-badge {status_class}">{status_display}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_ticket_actions(ticket_state: Dict[str, Any], ticket_id: str, customer_id: str):
    """Display action buttons for customer ticket management"""
    status = ticket_state.get('status', '').upper()
    
    if status not in ['CLOSED', 'RESOLVED']:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Resolve Ticket", use_container_width=True, key=f"resolve_{ticket_id}"):
                with st.spinner("Resolving ticket..."):
                    if run_async(mark_ticket_resolved(ticket_id, customer_id)):
                        st.success("Ticket resolved!")
                        st.rerun()

        with col2:
            if st.button("Close Ticket", use_container_width=True, key=f"close_{ticket_id}"):
                with st.spinner("Closing ticket..."):
                    if run_async(close_ticket_by_customer(ticket_id, customer_id)):
                        st.success("Ticket closed!")
                        st.rerun()


@st.fragment(run_every=AUTO_REFRESH_INTERVAL)
def display_ticket_view(ticket_id: str, customer_id: str):
    """Display ticket view with auto-refresh for active tickets using Streamlit fragments"""
    # Track ticket changes
    if 'last_seen_ticket_id' not in st.session_state:
        st.session_state.last_seen_ticket_id = None
    if 'last_message_count' not in st.session_state:
        st.session_state.last_message_count = 0
        
    if st.session_state.last_seen_ticket_id != ticket_id:
        st.session_state.last_message_count = 0
        st.session_state.last_seen_ticket_id = ticket_id
    
    # Get current ticket state
    ticket_state = run_async(get_ticket_state(ticket_id))
    
    if not ticket_state:
        if 'current_ticket_status' in st.session_state:
            st.session_state.current_ticket_status = None
        st.error("Unable to load ticket information. Please try again.")
        return
    
    # Check status and stop auto-refresh if ticket is closed/resolved
    status = ticket_state.get('status', '').upper()
    st.session_state.current_ticket_status = status
    
    # Display ticket header
    display_ticket_header(ticket_state)
    
    # Display chat history
    chat_history = ticket_state.get('chat_history', [])
    current_message_count = len(chat_history)
    pending_questions = ticket_state.get('pending_questions', {})
    
    st.markdown("### Conversation")
    display_chat_history(chat_history, pending_questions, ticket_id)
    
    # Message input (only if ticket is not closed/resolved)
    if status not in ['CLOSED', 'RESOLVED']:
        input_key = f"chat_input_{ticket_id}"
        clear_flag_key = f"__clear_{input_key}"

        if st.session_state.get(clear_flag_key):
            st.session_state.pop(input_key, None)
            st.session_state.pop(clear_flag_key, None)

        new_message = st.chat_input("Send a message to support…", key=input_key)

        if new_message and new_message.strip():
            with st.spinner("Sending message..."):
                if run_async(send_message_to_ticket(ticket_id, new_message.strip(), customer_id)):
                    st.success("Message sent!")
                    st.session_state[clear_flag_key] = True
                    st.rerun(scope="fragment")  # Rerun just this fragment immediately
        
        # Display ticket actions below the chat input
        display_ticket_actions(ticket_state, ticket_id, customer_id)
    else:
        st.info(f"This ticket is {status.lower()} and cannot receive new messages.")
    
    # Update message count tracking
    if current_message_count != st.session_state.last_message_count:
        st.session_state.last_message_count = current_message_count


def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Customer Support Portal</h1>
        <p>Get help from our AI-powered support team</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Live updates auto-refresh every {AUTO_REFRESH_INTERVAL}. Your ticket status will update in real time.")
    
    # Initialize session state
    if 'current_ticket_id' not in st.session_state:
        st.session_state.current_ticket_id = None
    if 'customer_id' not in st.session_state:
        st.session_state.customer_id = None
    if 'last_message_count' not in st.session_state:
        st.session_state.last_message_count = 0
    if 'current_ticket_status' not in st.session_state:
        st.session_state.current_ticket_status = None
    if 'last_seen_ticket_id' not in st.session_state:
        st.session_state.last_seen_ticket_id = None

    # Sidebar - Customer Selection and Ticket Management
    with st.sidebar:
        st.header("Customer Profile")
        
        # Customer selection
        customers = get_customers()
        customer_options = list(customers.keys())
        selected_customer = st.selectbox(
            "Select Customer ID:",
            customer_options,
            key="customer_selector"
        )
        
        if selected_customer:
            st.session_state.customer_id = selected_customer
            customer_info = customers[selected_customer]
            
            st.markdown(f"""
            **Name:** {customer_info['name']}  
            **Email:** {customer_info['email']}  
            **Tier:** {customer_info['tier']}
            """)
            
            st.divider()

            # Ticket management
            st.header("Your Tickets")

            customer_tickets = run_async(list_customer_tickets(st.session_state.customer_id))
            ticket_lookup = {ticket["ticket_id"]: ticket for ticket in customer_tickets if ticket.get("ticket_id")}

            ticket_option_ids = ["__NEW__"] + list(ticket_lookup.keys())

            pending_selection = st.session_state.get("pending_ticket_selection")
            if pending_selection and pending_selection not in ticket_option_ids:
                ticket_option_ids.append(pending_selection)

            current_selection = st.session_state.get("ticket_selector")
            if pending_selection:
                current_selection = pending_selection
            elif not current_selection or current_selection not in ticket_option_ids:
                if st.session_state.get('current_ticket_id') and st.session_state.current_ticket_id not in [None, "NEW"]:
                    current_selection = st.session_state.current_ticket_id
                else:
                    current_selection = "__NEW__"

            if current_selection and current_selection not in ticket_option_ids:
                ticket_option_ids.append(current_selection)

            if current_selection:
                st.session_state.ticket_selector = current_selection

            if pending_selection:
                st.session_state.pop("pending_ticket_selection", None)

            def _format_ticket_option(value: str) -> str:
                if value == "__NEW__":
                    return "Create New Ticket"
                ticket = ticket_lookup.get(value, {})
                status = (ticket.get("status") or "Unknown").replace('_', ' ').title()
                updated = ticket.get("last_updated") or ""
                return f"{value} • {status}{f' • {updated}' if updated else ''}"

            selected_ticket = st.selectbox(
                "Select Ticket:",
                ticket_option_ids,
                key="ticket_selector",
                format_func=_format_ticket_option
            )

            if selected_ticket == "__NEW__":
                st.session_state.current_ticket_id = "NEW"
            else:
                st.session_state.current_ticket_id = selected_ticket

    # Main Content Area
    if not st.session_state.customer_id:
        st.info("Please select a customer profile from the sidebar to begin.")
        return

    # Provide a quick overview of the customer's tickets and recent activity
    customer_ticket_overview = run_async(list_customer_tickets(st.session_state.customer_id))
    if customer_ticket_overview:
        open_count = sum(1 for ticket in customer_ticket_overview if (ticket.get("status") or "").lower() == TicketStatus.OPEN.value)
        in_progress_count = sum(1 for ticket in customer_ticket_overview if (ticket.get("status") or "").lower() == TicketStatus.IN_PROGRESS.value)
        escalated_count = sum(1 for ticket in customer_ticket_overview if (ticket.get("status") or "").lower() == TicketStatus.ESCALATED_TO_HUMAN.value)
        resolved_count = sum(1 for ticket in customer_ticket_overview if (ticket.get("status") or "").lower() == TicketStatus.RESOLVED.value)

        latest_update = next((ticket for ticket in sorted(customer_ticket_overview, key=lambda t: t.get("last_updated") or "", reverse=True) if ticket.get("last_updated")), None)

        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        summary_col1.metric("Open", open_count)
        summary_col2.metric("In Progress", in_progress_count)
        summary_col3.metric("Escalated", escalated_count)
        summary_col4.metric("Resolved", resolved_count)

        if latest_update:
            st.caption(f"Most recent update • Ticket {latest_update.get('ticket_id')} at {latest_update.get('last_updated')}")
    else:
        st.caption("No active tickets yet. Create one using the sidebar to get started.")

    if st.session_state.current_ticket_id == "NEW":
        # New ticket creation
        st.session_state.current_ticket_status = None
        st.session_state.last_message_count = 0
        st.header("Create New Support Ticket")
        
        with st.form("new_ticket_form"):
            initial_message = st.text_area(
                "Describe your issue:",
                height=150,
                placeholder="Please provide details about your problem..."
            )
            
            submitted = st.form_submit_button("Create Ticket", type="primary")
            
            if submitted and initial_message.strip():
                customers = get_customers()
                customer_profile = customers[st.session_state.customer_id]
                
                with st.spinner("Creating your support ticket..."):
                    ticket_id = run_async(create_new_ticket(
                        st.session_state.customer_id,
                        initial_message,
                        customer_profile
                    ))
                    
                    if ticket_id:
                        st.session_state.current_ticket_id = ticket_id
                        st.session_state.pending_ticket_selection = ticket_id
                        st.session_state.last_message_count = 0
                        st.success(f"Ticket created successfully! ID: {ticket_id}")
                        st.rerun()

    elif st.session_state.current_ticket_id:
        # Existing ticket view with continuous polling using Streamlit fragments
        display_ticket_view(st.session_state.current_ticket_id, st.session_state.customer_id)

    else:
        # No ticket selected
        st.session_state.current_ticket_status = None
        st.info("Please select a ticket from the sidebar or create a new one.")


if __name__ == "__main__":
    main()