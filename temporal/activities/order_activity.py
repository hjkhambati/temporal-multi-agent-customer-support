"""Order Specialist Activity"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import OrderSpecialistInput, OrderSpecialistOutput
from data.base_models import AgentType

# Import MCP manager for dynamic tool loading
from mcp_integration import mcp_manager

# Import static tools (user interaction tools)
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
    """Order specialist agent using DSPy.React with MCP tools"""
    dspy.context(lm=_GLOBAL_LM)
    
    # Set workflow context for user interaction tools
    set_workflow_context(
        ticket_workflow_id=input_data.ticket_workflow_id,
        ticket_id=input_data.ticket_id,
        agent_type="ORDER_SPECIALIST"
    )
    
    # Get tools from MCP servers for this agent type
    # Include user interaction tools
    static_tools = [ask_user_question, validate_user_response]
    
    # Get MCP tools dynamically
    all_tools = await mcp_manager.get_tools_for_agent(
        AgentType.ORDER_SPECIALIST,
        include_static_tools=static_tools
    )
    activity.logger.info(f"Order specialist using {len(all_tools)} tools from MCP")
    
    # Create React module with dynamically loaded tools
    order_react = dspy.ReAct(
        OrderSpecialistResponse,
        tools=all_tools
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