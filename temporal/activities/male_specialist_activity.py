"""Male Specialist Activity - Handle male clothing measurements and purchases"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import MaleSpecialistInput, MaleSpecialistOutput

# Import tools
from activities.tools.male_specialist_tools import (
    list_male_shirts_inventory,
    get_male_product_details,
    get_male_measurement_requirements,
    validate_male_measurements,
    record_male_measurements,
    retrieve_male_measurements,
    recommend_size_male
)
from activities.tools.user_interaction_tools import ask_user_question, validate_user_response, set_workflow_context

class MaleSpecialistResponse(dspy.Signature):
    """
    MALE SPECIALIST AGENT - Your responsibilities:
    
    1. Show available male shirts/clothing from inventory using list_male_shirts_inventory()
    2. Help customer select product (ask which one they want)
    3. Collect required measurements:
       - Chest circumference (inches)
       - Waist circumference (inches)
       - Shoulder width (inches)
       - Sleeve length (inches)
       - Neck circumference (inches)
    4. Validate measurements are realistic (use validate_male_measurements tool)
    5. Recommend appropriate size based on measurements (use recommend_size_male tool)
    6. Ask for color preference from available colors
    7. Save measurements using record_male_measurements tool
    8. Confirm final selection: product name, size, color
    
    CRITICAL: DO NOT create purchase orders - that's the billing agent's job!
    Your job ends after confirming the selection details.
    
    End with: "Perfect! I've recorded your preferences:
    - Product: [name]
    - Size: [size]
    - Color: [color]
    - Measurements saved
    The billing agent will now process your payment."
    """
    purchase_request: str = dspy.InputField()
    conversation_context: str = dspy.InputField()
    customer_id: str = dspy.InputField()
    customer_profile: str = dspy.InputField()
    
    response: str = dspy.OutputField(desc="Male specialist response")
    confidence: float = dspy.OutputField(desc="Response confidence 0-1")
    requires_escalation: bool = dspy.OutputField(desc="Needs human intervention")
    measurements_collected: bool = dspy.OutputField(desc="Whether measurements are collected")
    measurements_data: str = dspy.OutputField(desc="JSON string of measurements")
    validation_status: str = dspy.OutputField(desc="Measurement validation status")

# Global LM configuration
_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")

@activity.defn
async def male_specialist_activity(input_data: MaleSpecialistInput) -> MaleSpecialistOutput:
    """Male specialist agent using DSPy.React with measurement tools"""
    dspy.context(lm=_GLOBAL_LM)
    
    # Set workflow context for user interaction tools
    set_workflow_context(
        ticket_workflow_id=input_data.ticket_workflow_id,
        ticket_id=input_data.ticket_id,
        agent_type="MALE_SPECIALIST"
    )
    
    # Create React module with male specialist tools + user interaction
    male_react = dspy.ReAct(
        MaleSpecialistResponse,
        tools=[
            list_male_shirts_inventory,  # List available male shirts
            get_male_product_details,  # Get specific product details
            get_male_measurement_requirements,  # Get measurement requirements
            validate_male_measurements,  # Validate measurements
            record_male_measurements,  # Save measurements to file
            retrieve_male_measurements,  # Retrieve saved measurements
            recommend_size_male,  # Recommend size based on measurements
            ask_user_question,  # Ask clarifying questions to customer
            validate_user_response  # Validate customer responses
        ]
    )
    
    # Convert customer_profile dict to string for ReAct compatibility
    customer_profile_str = str(input_data.customer_profile) if input_data.customer_profile else "No profile data available"
    
    result = await male_react.acall(
        purchase_request=input_data.purchase_request,
        conversation_context=input_data.conversation_context,
        customer_id=input_data.customer_id,
        customer_profile=customer_profile_str
    )

    serialized_history = capture_llm_history()
    
    return MaleSpecialistOutput(
        response=result.response,
        confidence=float(result.confidence),
        requires_escalation=result.requires_escalation,
        measurements_collected=result.measurements_collected,
        measurements_data=result.measurements_data,
        validation_status=result.validation_status,
        llm_history=serialized_history,
        tool_results=getattr(result, 'tool_results', {})
    )
