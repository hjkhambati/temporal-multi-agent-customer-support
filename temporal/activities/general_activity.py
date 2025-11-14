"""General Support Activity"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import GeneralSupportInput, GeneralSupportOutput
from data.base_models import AgentType

# Import MCP manager for dynamic tool loading
from mcp_integration import mcp_manager

# Import static tools (user interaction tools)
from activities.tools.user_interaction_tools import ask_user_question, validate_user_response, set_workflow_context

class GeneralSupportResponse(dspy.Signature):
    """
    GENERAL SUPPORT AGENT - Your responsibilities:
    
    1. Answer general inquiries about the business, policies, and services
    2. Search FAQ database for common questions (use search_faq_tool)
    3. Get customer account information when needed (use get_account_info)
    4. Update customer preferences if requested (use update_customer_preferences)
    5. Provide business hours and service status (use get_business_hours, check_service_status)
    6. Schedule callbacks for complex issues (use schedule_callback)
    7. Create support tickets for issues that need follow-up (use create_support_ticket)
    
    CRITICAL: You are the first line of support for general inquiries.
    Be friendly, helpful, and thorough in answering questions.
    If the issue is specialized (orders, refunds, technical), recommend escalation.
    Always check FAQ first before creating tickets.
    
    End with helpful summary and next steps if applicable.
    """
    customer_message: str = dspy.InputField()
    conversation_context: str = dspy.InputField()
    customer_id: str = dspy.InputField()
    customer_profile: str = dspy.InputField()
    
    response: str = dspy.OutputField(desc="General support response")
    confidence: float = dspy.OutputField(desc="Response confidence")
    requires_escalation: bool = dspy.OutputField(desc="Needs human intervention")
    suggested_actions: str = dspy.OutputField(desc="Follow-up actions")

# Global LM configuration
_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")

@activity.defn
async def general_support_activity(input_data: GeneralSupportInput) -> GeneralSupportOutput:
    """General support agent using DSPy.React with general tools"""
    dspy.context(lm=_GLOBAL_LM)
    
    # Set workflow context for user interaction tools
    set_workflow_context(
        ticket_workflow_id=input_data.ticket_workflow_id,
        ticket_id=input_data.ticket_id,
        agent_type="GENERAL_SUPPORT"
    )
    
    # Get tools from MCP servers for this agent type
    static_tools = [ask_user_question, validate_user_response]
    
    all_tools = await mcp_manager.get_tools_for_agent(
        AgentType.GENERAL_SUPPORT,
        include_static_tools=static_tools
    )
    activity.logger.info(f"General support using {len(all_tools)} tools from MCP")
    
    # Create React module with dynamically loaded tools
    general_react = dspy.ReAct(
        GeneralSupportResponse,
        tools=all_tools
    )
    
    # Convert customer_profile dict to string for ReAct compatibility
    customer_profile_str = str(input_data.customer_profile) if input_data.customer_profile else "No profile data available"
    
    result = await general_react.acall(
        customer_message=input_data.customer_message,
        conversation_context=input_data.conversation_context,
        customer_id=input_data.customer_id,
        customer_profile=customer_profile_str
    )

    serialized_history = capture_llm_history()
    
    return GeneralSupportOutput(
        response=result.response,
        confidence=float(result.confidence),
        requires_escalation=result.requires_escalation,
        suggested_actions=result.suggested_actions,  # Now expects str, not list
        llm_history=serialized_history,
        tool_results=getattr(result, 'tool_results', {})
    )