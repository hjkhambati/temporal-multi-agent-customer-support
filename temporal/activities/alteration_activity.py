"""Alteration Activity - Handle clothing alteration requests"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import AlterationInput, AlterationOutput

# Import tools
from activities.tools.alteration_tools import (
    get_available_alterations,
    check_alteration_feasibility,
    calculate_alteration_cost,
    request_alteration,
    get_alteration_status,
    cancel_alteration
)
from activities.tools.user_interaction_tools import ask_user_question, validate_user_response, set_workflow_context

class AlterationResponse(dspy.Signature):
    """
    ALTERATION AGENT - Your responsibilities:
    
    1. Review the purchased item details from conversation context
    2. Ask customer what specific alterations they need:
       - Sleeve shortening/lengthening
       - Waist adjustment (take in/let out)
       - Length adjustment (hem)
       - Shoulder adjustment
       - Other custom alterations
    3. Check if alterations are feasible for the product (use check_alteration_feasibility tool)
    4. Calculate alteration costs (use calculate_alteration_cost tool):
       - Basic alterations: $15-$25
       - Complex alterations: $30-$50
       - Multiple alterations: Combined pricing
    5. Create alteration request with details (use request_alteration tool)
    6. Confirm total cost (product + alterations) and timeline (usually 5-7 days)
    
    CRITICAL: Only offer alterations marked as "alterable" in the product catalog.
    Be clear about costs before creating alteration request.
    Explain that alterations add 5-7 business days to delivery time.
    
    End with: "Alteration request created!
    - Alterations: [list of alterations]
    - Additional Cost: $[amount]
    - Timeline: +5-7 business days
    - Total: $[product + alterations]"
    """
    purchase_request: str = dspy.InputField()
    conversation_context: str = dspy.InputField()
    customer_id: str = dspy.InputField()
    customer_profile: str = dspy.InputField()
    
    response: str = dspy.OutputField(desc="Alteration agent response")
    confidence: float = dspy.OutputField(desc="Response confidence 0-1")
    requires_escalation: bool = dspy.OutputField(desc="Needs human intervention")
    alteration_needed: bool = dspy.OutputField(desc="Whether alteration is needed")
    alteration_details: str = dspy.OutputField(desc="Details of alterations")
    additional_cost: float = dspy.OutputField(desc="Additional cost for alterations")

# Global LM configuration
_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")

@activity.defn
async def alteration_activity(input_data: AlterationInput) -> AlterationOutput:
    """Alteration agent using DSPy.React with alteration tools"""
    dspy.context(lm=_GLOBAL_LM)
    
    # Set workflow context for user interaction tools
    set_workflow_context(
        ticket_workflow_id=input_data.ticket_workflow_id,
        ticket_id=input_data.ticket_id,
        agent_type="ALTERATION"
    )
    
    # Create React module with alteration tools + user interaction
    alteration_react = dspy.ReAct(
        AlterationResponse,
        tools=[
            get_available_alterations,
            check_alteration_feasibility,
            calculate_alteration_cost,
            request_alteration,
            get_alteration_status,
            cancel_alteration,
            ask_user_question,  # Allow agent to ask clarifying questions
            validate_user_response
        ]
    )
    
    # Convert customer_profile dict to string for ReAct compatibility
    customer_profile_str = str(input_data.customer_profile) if input_data.customer_profile else "No profile data available"
    
    result = await alteration_react.acall(
        purchase_request=input_data.purchase_request,
        conversation_context=input_data.conversation_context,
        customer_id=input_data.customer_id,
        customer_profile=customer_profile_str
    )

    serialized_history = capture_llm_history()
    
    return AlterationOutput(
        response=result.response,
        confidence=float(result.confidence),
        requires_escalation=result.requires_escalation,
        alteration_needed=result.alteration_needed,
        alteration_details=result.alteration_details,
        additional_cost=float(result.additional_cost),
        llm_history=serialized_history,
        tool_results=getattr(result, 'tool_results', {})
    )
