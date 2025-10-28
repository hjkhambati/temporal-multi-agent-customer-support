"""Order Specialist Activity"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import OrderSpecialistInput, OrderSpecialistOutput

# Import tools
from activities.tools.order_tools import search_orders, check_order_status, modify_order, get_order_history, calculate_shipping_cost
from activities.tools.user_interaction_tools import ask_user_question, validate_user_response, set_workflow_context

class OrderSpecialistResponse(dspy.Signature):
    """
    ORDER SPECIALIST AGENT - Your responsibilities:
    
    1. Search for customer orders (use search_orders tool)
    2. Check order status and tracking information (use check_order_status)
    3. Provide order history for customer (use get_order_history)
    4. Modify orders if possible (use modify_order - only if order not shipped)
    5. Calculate shipping costs for inquiries (use calculate_shipping_cost)
    6. Answer questions about order timeline, tracking, and delivery
    
    CRITICAL: You handle existing order inquiries (NOT new purchases).
    For new purchases, customer should be directed to male/female specialists.
    Always verify order belongs to the customer before sharing details.
    Only modify orders that haven't shipped yet.
    
    End with order status summary and tracking information if available.
    """
    customer_message: str = dspy.InputField()
    conversation_context: str = dspy.InputField()
    customer_id: str = dspy.InputField()
    customer_profile: str = dspy.InputField()
    
    response: str = dspy.OutputField(desc="Customer service response")
    confidence: float = dspy.OutputField(desc="Response confidence")
    requires_escalation: bool = dspy.OutputField(desc="Needs human intervention")
    suggested_actions: str = dspy.OutputField(desc="Follow-up actions")

# Global LM configuration
_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")

@activity.defn
async def order_specialist_activity(input_data: OrderSpecialistInput) -> OrderSpecialistOutput:
    """Order specialist agent using DSPy.React with order tools"""
    dspy.context(lm=_GLOBAL_LM)
    
    # Set workflow context for user interaction tools
    set_workflow_context(
        ticket_workflow_id=input_data.ticket_workflow_id,
        ticket_id=input_data.ticket_id,
        agent_type="ORDER_SPECIALIST"
    )
    
    # Create React module with order tools + user interaction - agents will autonomously use tools as needed
    order_react = dspy.ReAct(
        OrderSpecialistResponse,
        tools=[
            search_orders, 
            check_order_status, 
            modify_order, 
            get_order_history, 
            calculate_shipping_cost,
            ask_user_question,  # Allow agent to ask clarifying questions
            validate_user_response
        ]
    )
    
    # Convert customer_profile dict to string for ReAct compatibility
    customer_profile_str = str(input_data.customer_profile) if input_data.customer_profile else "No profile data available"
    
    result = await order_react.acall(
        customer_message=input_data.customer_message,
        conversation_context=input_data.conversation_context,
        customer_id=input_data.customer_id,
        customer_profile=customer_profile_str
    )

    serialized_history = capture_llm_history()
    
    return OrderSpecialistOutput(
        response=result.response,
        confidence=float(result.confidence),
        requires_escalation=result.requires_escalation,
        suggested_actions=result.suggested_actions,  # Now expects str, not list
        llm_history=serialized_history,
        tool_results=getattr(result, 'tool_results', {})
    )