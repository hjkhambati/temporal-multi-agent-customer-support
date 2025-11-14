"""Delivery Activity - Handle shipping, tracking, and delivery scheduling"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import DeliveryInput, DeliveryOutput
from data.base_models import AgentType

# Import MCP manager for dynamic tool loading
from mcp_integration import mcp_manager

# Import static tools (user interaction tools)
from activities.tools.user_interaction_tools import ask_user_question, validate_user_response, set_workflow_context

class DeliveryResponse(dspy.Signature):
    """
    DELIVERY AGENT - Your responsibilities:
    
    1. Get customer's complete delivery address (use ask_user_question if not provided)
    2. Validate address is complete and deliverable (use validate_delivery_address tool)
    3. Present delivery options to customer:
       - Standard (5-7 business days) - FREE
       - Express (2-3 business days) - $15
       - Overnight (next business day) - $35
    4. Calculate estimated delivery dates for each option (use calculate_delivery_date tool)
    5. Schedule delivery with customer's chosen option (use schedule_purchase_delivery tool)
    6. Provide tracking number to customer
    7. Confirm delivery details (address, date, tracking number)
    
    CRITICAL: Ensure address is complete (street, city, state, zip) before scheduling.
    Use get_delivery_options() to show available options.
    Always provide tracking number after scheduling.
    
    End with: "Delivery scheduled! 
    - Address: [full address]
    - Delivery Option: [option name]
    - Expected Delivery: [date]
    - Tracking Number: [number]"
    """
    purchase_request: str = dspy.InputField()
    conversation_context: str = dspy.InputField()
    customer_id: str = dspy.InputField()
    customer_profile: str = dspy.InputField()
    
    response: str = dspy.OutputField(desc="Delivery agent response")
    confidence: float = dspy.OutputField(desc="Response confidence 0-1")
    requires_escalation: bool = dspy.OutputField(desc="Needs human intervention")
    delivery_scheduled: bool = dspy.OutputField(desc="Whether delivery is scheduled")
    delivery_date: str = dspy.OutputField(desc="Scheduled delivery date")
    tracking_number: str = dspy.OutputField(desc="Tracking number")
    delivery_address: str = dspy.OutputField(desc="Delivery address")

# Global LM configuration
_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")

@activity.defn
async def delivery_activity(input_data: DeliveryInput) -> DeliveryOutput:
    """Delivery agent using DSPy.React with delivery tools"""
    dspy.context(lm=_GLOBAL_LM)
    
    # Set workflow context for user interaction tools
    set_workflow_context(
        ticket_workflow_id=input_data.ticket_workflow_id,
        ticket_id=input_data.ticket_id,
        agent_type="DELIVERY"
    )
    
    # Get tools from MCP servers for this agent type
    static_tools = [ask_user_question, validate_user_response]
    
    all_tools = await mcp_manager.get_tools_for_agent(
        AgentType.DELIVERY,
        include_static_tools=static_tools
    )
    activity.logger.info(f"Delivery agent using {len(all_tools)} tools from MCP")
    
    # Create React module with dynamically loaded tools
    delivery_react = dspy.ReAct(
        DeliveryResponse,
        tools=all_tools
    )
    
    # Convert customer_profile dict to string for ReAct compatibility
    customer_profile_str = str(input_data.customer_profile) if input_data.customer_profile else "No profile data available"
    
    result = await delivery_react.acall(
        purchase_request=input_data.purchase_request,
        conversation_context=input_data.conversation_context,
        customer_id=input_data.customer_id,
        customer_profile=customer_profile_str
    )

    serialized_history = capture_llm_history()
    
    return DeliveryOutput(
        response=result.response,
        confidence=float(result.confidence),
        requires_escalation=result.requires_escalation,
        delivery_scheduled=result.delivery_scheduled,
        delivery_date=result.delivery_date,
        tracking_number=result.tracking_number,
        delivery_address=result.delivery_address,
        llm_history=serialized_history,
        tool_results=getattr(result, 'tool_results', {})
    )
