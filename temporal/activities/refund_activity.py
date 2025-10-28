"""Refund Specialist Activity"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import RefundSpecialistInput, RefundSpecialistOutput

# Import tools
from activities.tools.refund_tools import check_refund_eligibility, calculate_refund_amount, initiate_refund, generate_return_label, check_return_status, get_return_policy_details
from activities.tools.user_interaction_tools import ask_user_question, validate_user_response, set_workflow_context

class RefundSpecialistResponse(dspy.Signature):
    """
    REFUND SPECIALIST AGENT - Your responsibilities:
    
    1. Get order ID for the refund request (ask customer or search orders)
    2. Check refund eligibility based on policy (use check_refund_eligibility tool):
       - Within 30 days of purchase
       - Item unused and in original packaging
       - Receipt or order confirmation available
    3. Get return policy details if needed (use get_return_policy_details)
    4. Calculate refund amount (use calculate_refund_amount - includes shipping deductions if applicable)
    5. Initiate refund process (use initiate_refund tool)
    6. Generate return shipping label (use generate_return_label)
    7. Explain return process and timeline:
       - Return item with provided label
       - Processing takes 5-7 business days after receipt
       - Refund issued to original payment method
    
    CRITICAL: Always check eligibility first before promising refunds.
    Be empathetic but firm about policy requirements.
    Provide clear instructions for returning items.
    
    End with: "Refund approved! 
    - Amount: $[amount]
    - Return label: [label ID]
    - Timeline: 5-7 business days after we receive the item"
    """
    refund_request: str = dspy.InputField()
    conversation_context: str = dspy.InputField()
    customer_id: str = dspy.InputField()
    customer_profile: str = dspy.InputField()
    
    response: str = dspy.OutputField(desc="Refund specialist response")
    confidence: float = dspy.OutputField(desc="Response confidence 0-1")
    requires_escalation: bool = dspy.OutputField(desc="Needs human intervention")
    eligibility_assessment: str = dspy.OutputField(desc="Refund eligibility status")
    required_documentation: str = dspy.OutputField(desc="Documents needed")
    processing_timeline: str = dspy.OutputField(desc="Expected processing time")

# Global LM configuration
_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")

@activity.defn
async def refund_specialist_activity(input_data: RefundSpecialistInput) -> RefundSpecialistOutput:
    """Refund specialist agent using DSPy.React with refund tools"""
    dspy.context(lm=_GLOBAL_LM)
    
    # Set workflow context for user interaction tools
    set_workflow_context(
        ticket_workflow_id=input_data.ticket_workflow_id,
        ticket_id=input_data.ticket_id,
        agent_type="REFUND_SPECIALIST"
    )
    
    # Create React module with refund tools + user interaction - agent will autonomously use tools and policies
    refund_react = dspy.ReAct(
        RefundSpecialistResponse,
        tools=[
            check_refund_eligibility, 
            calculate_refund_amount, 
            initiate_refund, 
            generate_return_label, 
            check_return_status, 
            get_return_policy_details,
            ask_user_question,  # Allow agent to ask clarifying questions
            validate_user_response
        ]
    )
    
    # Convert customer_profile dict to string for ReAct compatibility
    customer_profile_str = str(input_data.customer_profile) if input_data.customer_profile else "No profile data available"
    
    result = await refund_react.acall(
        refund_request=input_data.refund_request,
        conversation_context=input_data.conversation_context,
        customer_id=input_data.customer_id,
        customer_profile=customer_profile_str
    )

    serialized_history = capture_llm_history()
    
    return RefundSpecialistOutput(
        response=result.response,
        confidence=float(result.confidence),
        requires_escalation=result.requires_escalation,
        eligibility_assessment=result.eligibility_assessment,
        required_documentation=result.required_documentation,  # Now expects str, not list
        processing_timeline=result.processing_timeline,
        llm_history=serialized_history,
        tool_results=getattr(result, 'tool_results', {})
    )