"""
Improved Admin Support Interface with Proper Polling and Enhanced Features
"""
import streamlit as st
import asyncio
import nest_asyncio
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from temporalio.client import Client
from temporal.data.base_models import MessageType, AgentType, TicketStatus
from temporal.data.ticket_models import ChatMessage

# Configuration
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TASK_QUEUE = os.getenv("TASK_QUEUE", "multi-agent-support")
AUTO_REFRESH_INTERVAL = "3s"  # Streamlit fragment format (e.g., "3s", "1000ms")

def run_async(coro):
    """Run async function synchronously"""
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
    page_title="Admin Support Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.stApp {
    background-color: #f9fafb;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.main .block-container {
    max-width: 1400px;
    padding-top: 1.5rem;
}

.admin-header {
    background: #ffffff;
    color: #1f2937;
    padding: 2rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    text-align: center;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.admin-header h1 {
    color: #1f2937;
    font-weight: 700;
    margin: 0;
    font-size: 2rem;
}

.admin-header p {
    color: #6b7280;
    margin: 0.5rem 0 0 0;
}

.metric-card {
    background: linear-gradient(135deg, #ffffff 0%, #f3f4f6 100%);
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 12px 20px -16px rgba(15, 23, 42, 0.45);
    border: 1px solid rgba(148, 163, 184, 0.25);
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    min-height: 120px;
}

.metric-card .metric-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #64748b;
}

.metric-card .metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
}

.metric-card.metric-urgent {
    border: 1px solid rgba(220, 38, 38, 0.2);
    background: linear-gradient(135deg, rgba(254, 242, 242, 0.9) 0%, rgba(254, 226, 226, 0.8) 100%);
}

.metric-card.metric-urgent .metric-value {
    color: #b91c1c;
}

.metric-card.metric-progress {
    border: 1px solid rgba(59, 130, 246, 0.2);
    background: linear-gradient(135deg, rgba(239, 246, 255, 0.95) 0%, rgba(219, 234, 254, 0.8) 100%);
}

.metric-card.metric-progress .metric-value {
    color: #1d4ed8;
}

.metric-card.metric-success {
    border: 1px solid rgba(34, 197, 94, 0.2);
    background: linear-gradient(135deg, rgba(240, 253, 244, 0.95) 0%, rgba(220, 252, 231, 0.85) 100%);
}

.metric-card.metric-success .metric-value {
    color: #15803d;
}

.metric-card.metric-total {
    border: 1px solid rgba(79, 70, 229, 0.12);
    background: linear-gradient(135deg, rgba(237, 233, 254, 0.9) 0%, rgba(224, 231, 255, 0.85) 100%);
}

.metric-card.metric-total .metric-value {
    color: #4338ca;
}

.ticket-card {
    background: #ffffff;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.75rem 0;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
    border-left-width: 3px;
    cursor: pointer;
    transition: transform 0.1s;
}

.ticket-card:hover {
    transform: translateX(4px);
}

.ticket-card.escalated {
    border-left-color: #dc2626;
}

.ticket-card.in-progress {
    border-left-color: #2563eb;
}

.ticket-card.resolved {
    border-left-color: #16a34a;
}

.ticket-card.closed {
    border-left-color: #6b7280;
}

.chat-container {
    background: #ffffff;
    border-radius: 12px;
    padding: 1.5rem;
    max-height: 500px;
    overflow-y: auto;
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

.message-wrapper.customer {
    justify-content: flex-start;
}

.message-wrapper.agent {
    justify-content: flex-end;
}

.chat-message {
    max-width: 75%;
    padding: 0.875rem 1.125rem;
    border-radius: 12px;
    line-height: 1.5;
}

.customer-message {
    background: #f3f4f6;
    color: #1f2937;
    border: 1px solid #e5e7eb;
}

.agent-message {
    background: #2563eb;
    color: white;
}

.admin-message {
    background: #7c3aed;
    color: white;
}

.message-meta {
    font-size: 0.8125rem;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.customer-message .message-meta {
    color: #6b7280;
}

.agent-message .message-meta,
.admin-message .message-meta {
    color: rgba(255, 255, 255, 0.9);
}

.status-badge {
    padding: 0.25rem 0.625rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.status-open { background: #dcfce7; color: #166534; }
.status-in-progress { background: #dbeafe; color: #1e40af; }
.status-escalated-to-human { background: #fee2e2; color: #991b1b; }
.status-resolved { background: #f3f4f6; color: #374151; }
.status-closed { background: #f3f4f6; color: #374151; }

footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Core async functions
async def list_active_workflows() -> List[Dict[str, Any]]:
    """List all active workflow executions"""
    try:
        client = get_temporal_client()
        workflows = []
        async for workflow in client.list_workflows("WorkflowType='TicketWorkflow'"):
            workflows.append({
                'id': workflow.id,
                'run_id': workflow.run_id,
                'type': workflow.workflow_type,
                'start_time': workflow.start_time
            })
        return workflows
    except Exception as e:
        st.error(f"Failed to list workflows: {str(e)}")
        return []

async def get_ticket_details(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed ticket information"""
    try:
        client = get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        state = await handle.query("getState")
        return state
    except Exception as e:
        return {
            "ticket_id": workflow_id,
            "status": "ERROR",
            "customer_id": "Unknown",
            "error": str(e)
        }

async def send_admin_response(ticket_id: str, message: str, admin_name: str) -> bool:
    """Send admin response to a ticket"""
    try:
        client = get_temporal_client()
        handle = client.get_workflow_handle(ticket_id)
        
        chat_message = ChatMessage(
            id=f"admin-msg-{datetime.now().timestamp()}",
            ticket_id=ticket_id,
            content=message,
            message_type=MessageType.HUMAN_AGENT,
            agent_type=AgentType.HUMAN_AGENT,
            timestamp=datetime.now()
        )
        
        await handle.signal("addMessage", chat_message.to_dict())
        return True
    except Exception as e:
        st.error(f"Failed to send response: {str(e)}")
        print(f"DEBUG - Send error: {e}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        return False

async def resolve_ticket(ticket_id: str, resolution_summary: str | None = None) -> bool:
    """Mark ticket as resolved without injecting additional chat messages."""
    try:
        client = get_temporal_client()
        handle = client.get_workflow_handle(ticket_id)
        
        await handle.signal("updateTicketStatus", "resolved")
        return True
    except Exception as e:
        st.error(f"Failed to resolve ticket: {str(e)}")
        print(f"DEBUG - Resolve error: {e}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        return False

async def close_ticket(ticket_id: str, close_reason: str | None = None) -> bool:
    """Close ticket without sending chat updates."""
    try:
        client = get_temporal_client()
        handle = client.get_workflow_handle(ticket_id)
        
        await handle.signal("updateTicketStatus", "closed")
        return True
    except Exception as e:
        st.error(f"Failed to close ticket: {str(e)}")
        return False

def display_ticket_metrics(tickets: List[Dict[str, Any]], ticket_details: List[Dict[str, Any]]):
    """Display ticket metrics"""
    def _status(detail: Dict[str, Any]) -> str:
        return (detail.get('status') or '').lower() if detail else ''

    total_tickets = len(tickets)
    escalated_count = sum(1 for detail in ticket_details if _status(detail) == TicketStatus.ESCALATED_TO_HUMAN.value)
    in_progress_count = sum(1 for detail in ticket_details if _status(detail) == TicketStatus.IN_PROGRESS.value)
    resolved_count = sum(1 for detail in ticket_details if _status(detail) == TicketStatus.RESOLVED.value)

    metric_definitions = [
        ("Total Tickets", total_tickets, "metric-total"),
        ("Escalated", escalated_count, "metric-urgent"),
        ("In Progress", in_progress_count, "metric-progress"),
        ("Resolved", resolved_count, "metric-success"),
    ]

    columns = st.columns(len(metric_definitions))
    for column, (label, value, variant) in zip(columns, metric_definitions):
        with column:
            st.markdown(
                f"""
                <div class="metric-card {variant}">
                    <span class="metric-label">{label}</span>
                    <span class="metric-value">{value}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

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

def display_chat_interface(ticket_state: Dict[str, Any]):
    """Display chat interface using native Streamlit components"""
    st.markdown("### Ticket Conversation")
    
    if ticket_state.get('chat_history'):
        for message in ticket_state['chat_history']:
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
            
            # Determine message type
            is_customer = (
                message_type == 'CUSTOMER' or 
                message_type == 'customer' or 
                str(message_type) == 'MessageType.CUSTOMER'
            )
            
            is_human_agent = (
                message_type == 'HUMAN_AGENT' or
                message_type == 'human_agent' or
                str(message_type) == 'MessageType.HUMAN_AGENT'
            )
            
            if is_customer:
                with st.chat_message("user"):
                    st.write(f"**Customer** ({time_display})")
                    st.write(content)
            elif is_human_agent:
                with st.chat_message("assistant"):
                    st.write(f"**Admin Agent** ({time_display})")
                    st.write(content)
            else:
                # AI Agent
                agent_name = get_agent_display_name(agent_type)
                with st.chat_message("assistant"):
                    st.write(f"**{agent_name}** ({time_display})")
                    st.write(content)
                    
                    # Display additional structured information
                    if additional_info:
                        formatted_info = format_additional_info_text(agent_type, additional_info)
                        if formatted_info:
                            st.info(formatted_info)
    else:
        st.info("No messages in this ticket yet.")

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


@st.fragment(run_every=AUTO_REFRESH_INTERVAL)
def display_dashboard_content():
    """Auto-refreshing dashboard content using Streamlit fragments"""
    with st.spinner("Loading tickets..."):
        tickets = run_async(list_active_workflows())
        ticket_details: List[Dict[str, Any]] = []

        if tickets:
            for ticket in tickets:
                details = run_async(get_ticket_details(ticket['id']))
                if details:
                    ticket_details.append(details)

    # Main content
    tab1, tab2 = st.tabs(["Live Tickets", "Analytics"])

    with tab1:
        
        # Display metrics
        if tickets:
            display_ticket_metrics(tickets, ticket_details)
            st.markdown("""<div style="margin: 0.25rem 0 1rem 0; text-align: center; color: #6b7280;">
                Use the controls below to focus on the conversations that need your attention.
            </div>""", unsafe_allow_html=True)
            
            # Ticket list
            st.markdown("### Active Tickets")

            unique_statuses = sorted({(detail.get('status') or 'Unknown').replace('_', ' ').title() for detail in ticket_details})
            filter_options = ["All statuses"] + unique_statuses
            if 'admin_status_filter' not in st.session_state:
                st.session_state.admin_status_filter = "All statuses"

            status_filter = st.selectbox(
                "Filter by status",
                filter_options,
                key="admin_status_filter"
            )
            
            # Filter and sort tickets
            sorted_tickets = sorted(ticket_details, 
                                  key=lambda x: x.get('last_updated', ''), 
                                  reverse=True)

            if status_filter != "All statuses":
                status_match = status_filter.lower().replace(' ', '_')
                sorted_tickets = [ticket for ticket in sorted_tickets if (ticket.get('status') or '').lower() == status_match]
            
            for ticket_detail in sorted_tickets:
                if not ticket_detail:
                    continue
                    
                ticket_id = ticket_detail.get('ticket_id', 'Unknown')
                status = ticket_detail.get('status', 'Unknown')
                customer_id = ticket_detail.get('customer_id', 'Unknown')
                last_updated = ticket_detail.get('last_updated', '')
                
                # Create ticket card
                status_class = status.lower().replace('_', '-') if status else 'unknown'
                
                # Use columns for ticket selection
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="ticket-card {status_class}">
                        <h4>Ticket #{ticket_id}</h4>
                        <p><strong>Customer:</strong> {customer_id}</p>
                        <p><strong>Status:</strong> <span class="status-badge status-{status_class}">{status.replace('_', ' ').title()}</span></p>
                        <p><strong>Last Updated:</strong> {last_updated}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("Select", key=f"select_{ticket_id}"):
                        st.session_state.selected_ticket_id = ticket_id
                        st.session_state.admin_ticket_status = status.upper() if isinstance(status, str) else status
                        st.rerun(scope="fragment")
            
            # Selected ticket details
            if st.session_state.selected_ticket_id:
                st.divider()
                ticket_id = st.session_state.selected_ticket_id
                ticket_state = run_async(get_ticket_details(ticket_id))
                if not ticket_state:
                    st.warning("Ticket data is no longer available. It may have completed.")
                    st.session_state.selected_ticket_id = None
                    st.session_state.admin_ticket_status = None
                    st.rerun(scope="fragment")
                    return
                
                st.markdown(f"### Ticket Details: #{ticket_id}")
                
                # Display conversation
                display_chat_interface(ticket_state)
                
                # Admin response interface
                status = ticket_state.get('status', '').upper()
                st.session_state.admin_ticket_status = status
                if status not in ['CLOSED', 'RESOLVED']:
                    st.markdown("### Admin Actions")

                    response_key = f"admin_response_{ticket_id}"
                    response_clear_flag = f"__clear_{response_key}"

                    if st.session_state.get(response_clear_flag):
                        st.session_state.pop(response_key, None)
                        st.session_state.pop(response_clear_flag, None)

                    admin_response = st.chat_input("Send a response to the customer…", key=response_key)

                    if admin_response and admin_response.strip():
                        with st.spinner("Sending response..."):
                            if run_async(send_admin_response(ticket_id, admin_response.strip(), st.session_state.admin_name)):
                                st.success("Response sent successfully!")
                                st.session_state[response_clear_flag] = True
                                st.rerun(scope="fragment")

                    action_col1, action_col2 = st.columns(2)

                    with action_col1:
                        if st.button("Resolve Ticket", use_container_width=True, key=f"admin_resolve_{ticket_id}"):
                            with st.spinner("Resolving ticket..."):
                                if run_async(resolve_ticket(ticket_id)):
                                    st.success("Ticket resolved!")
                                    st.session_state.selected_ticket_id = None
                                    st.session_state.admin_ticket_status = None
                                    st.rerun(scope="fragment")

                    with action_col2:
                        if st.button("Close Ticket", use_container_width=True, key=f"admin_close_{ticket_id}"):
                            with st.spinner("Closing ticket..."):
                                if run_async(close_ticket(ticket_id)):
                                    st.success("Ticket closed!")
                                    st.session_state.selected_ticket_id = None
                                    st.session_state.admin_ticket_status = None
                                    st.rerun(scope="fragment")
                else:
                    st.info(f"This ticket is {status.lower()} and cannot be modified.")
            else:
                st.session_state.admin_ticket_status = None
        else:
            st.info("No active tickets found. Tickets will appear here when customers create them.")
    
    with tab2:
        st.header("Analytics Dashboard")
        st.caption("These insights refresh automatically alongside the live ticket feed.")

        if ticket_details:
            # Status distribution
            status_counts = {}
            for ticket in ticket_details:
                status = ticket.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            st.markdown("### Ticket Status Distribution")
            for status, count in status_counts.items():
                st.metric(status.replace('_', ' ').title(), count)
            
            # Recent activity
            st.markdown("### Recent Activity")
            recent_tickets = sorted(ticket_details, 
                                  key=lambda x: x.get('last_updated', ''), 
                                  reverse=True)[:5]
            
            for ticket in recent_tickets:
                st.write(f"- Ticket #{ticket.get('ticket_id', 'Unknown')} - {ticket.get('status', 'Unknown')}")
        else:
            st.info("No data available for analytics.")


def main():
    # Header
    st.markdown("""
    <div class="admin-header">
        <h1>Admin Support Dashboard</h1>
        <p>Real-time Customer Support Management</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Dashboard refreshes automatically every {AUTO_REFRESH_INTERVAL}. Responses and status changes apply instantly.")
    
    # Initialize session state
    if 'selected_ticket_id' not in st.session_state:
        st.session_state.selected_ticket_id = None
    if 'admin_name' not in st.session_state:
        st.session_state.admin_name = "Admin User"
    if 'admin_ticket_status' not in st.session_state:
        st.session_state.admin_ticket_status = None

    # Sidebar
    with st.sidebar:
        st.header("Admin Controls")
        
        st.session_state.admin_name = st.text_input(
            "Admin Name:",
            value=st.session_state.admin_name
        )
        
        st.divider()
        st.caption("Ticket list updates continuously; no manual refresh needed.")

    # Display auto-refreshing dashboard content
    display_dashboard_content()

if __name__ == "__main__":
    main()