"""Billing Activity - Handle payment processing and invoicing"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import BillingInput, BillingOutput

# Import tools
from activities.tools.billing_tools import (
    create_bill_from_conversation,
    calculate_purchase_total,
    apply_discount,
    get_customer_tier_discount,
    process_payment,
    generate_invoice,
    check_payment_status
)
from activities.tools.user_interaction_tools import ask_user_question, validate_user_response, set_workflow_context

class BillingResponse(dspy.Signature):
    """
    BILLING AGENT - Your responsibilities:
    
    1. Extract purchase details from conversation (product, size, color, price)
    2. Create a NEW purchase order
    3. Calculate total cost (item price + tax)
    4. Apply customer tier discount automatically (Gold/Platinum members)
    5. Process payment with customer's preferred payment method
    6. Generate invoice with all details and display them to user
    
    CRITICAL: You are receiving details from the purchase specialist (male/female).
    They have already collected product selection, measurements, size, and color.
    Your job is to CREATE THE BILL and process payment, NOT to ask for order IDs.
    
    The conversation_context contains all purchase details - extract them and create the bill.
    """
    purchase_request: str = dspy.InputField()
    conversation_context: str = dspy.InputField(desc="Full conversation with all purchase details from specialist")
    customer_id: str = dspy.InputField()
    customer_profile: str = dspy.InputField()
    
    response: str = dspy.OutputField(desc="Billing agent response to customer")
    confidence: float = dspy.OutputField(desc="Response confidence 0-1")
    requires_escalation: bool = dspy.OutputField(desc="Needs human intervention")
    billing_complete: bool = dspy.OutputField(desc="Whether billing is complete")
    total_amount: float = dspy.OutputField(desc="Total purchase amount")
    payment_status: str = dspy.OutputField(desc="Payment status")
    invoice_details: str = dspy.OutputField(desc="Invoice information")

# Global LM configuration
_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")

@activity.defn
async def billing_activity(input_data: BillingInput) -> BillingOutput:
    """Billing agent using DSPy.React with billing tools"""
    dspy.context(lm=_GLOBAL_LM)
    
    # Set workflow context for user interaction tools
    set_workflow_context(
        ticket_workflow_id=input_data.ticket_workflow_id,
        ticket_id=input_data.ticket_id,
        agent_type="BILLING"
    )
    
    # Create React module with billing tools + user interaction
    billing_react = dspy.ReAct(
        BillingResponse,
        tools=[
            create_bill_from_conversation,
            calculate_purchase_total,
            apply_discount,
            get_customer_tier_discount,
            process_payment,
            generate_invoice,
            check_payment_status,
            ask_user_question,
            validate_user_response
        ]
    )
    
    # Convert customer_profile dict to string for ReAct compatibility
    customer_profile_str = str(input_data.customer_profile) if input_data.customer_profile else "No profile data available"
    
    result = await billing_react.acall(
        purchase_request=input_data.purchase_request,
        conversation_context=input_data.conversation_context,
        customer_id=input_data.customer_id,
        customer_profile=customer_profile_str
    )

    serialized_history = capture_llm_history()
    
    return BillingOutput(
        response=result.response,
        confidence=float(result.confidence),
        requires_escalation=result.requires_escalation,
        billing_complete=result.billing_complete,
        total_amount=float(result.total_amount),
        payment_status=result.payment_status,
        invoice_details=result.invoice_details,
        llm_history=serialized_history,
        tool_results=getattr(result, 'tool_results', {})
    )
