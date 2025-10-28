"""Technical Specialist Activity"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import TechnicalSpecialistInput, TechnicalSpecialistOutput

# Import tools
from activities.tools.technical_tools import search_knowledge_base_tool, get_product_specs, check_warranty, create_escalation_ticket, run_diagnostics, check_firmware_updates
from activities.tools.user_interaction_tools import ask_user_question, validate_user_response, set_workflow_context

class TechnicalSpecialistResponse(dspy.Signature):
    """
    TECHNICAL SPECIALIST AGENT - Your responsibilities:
    
    1. Understand the technical issue from customer description
    2. Search knowledge base for similar issues and solutions (use search_knowledge_base_tool)
    3. Get product specifications if needed (use get_product_specs)
    4. Check warranty status for the product (use check_warranty)
    5. Run diagnostics if applicable (use run_diagnostics)
    6. Check for firmware/software updates (use check_firmware_updates)
    7. Provide step-by-step troubleshooting instructions
    8. Create escalation ticket if issue requires advanced support (use create_escalation_ticket)
    
    CRITICAL: Be clear and patient with technical instructions.
    Break down complex steps into simple, numbered instructions.
    Verify customer understanding after each major step.
    If issue can't be resolved remotely, escalate appropriately.
    
    End with: "Troubleshooting steps:
    1. [Step 1]
    2. [Step 2]
    3. [Step 3]
    Let me know if this resolves your issue or if you need further assistance."
    """
    issue_description: str = dspy.InputField()
    conversation_context: str = dspy.InputField()
    customer_id: str = dspy.InputField()
    customer_profile: str = dspy.InputField()
    
    response: str = dspy.OutputField(desc="Technical support response")
    confidence: float = dspy.OutputField(desc="Response confidence 0-1")
    requires_escalation: bool = dspy.OutputField(desc="Needs human technical expert")
    troubleshooting_steps: str = dspy.OutputField(desc="Step-by-step solution")
    estimated_resolution_time: str = dspy.OutputField(desc="Expected time to resolve")

# Global LM configuration
_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")

@activity.defn
async def technical_specialist_activity(input_data: TechnicalSpecialistInput) -> TechnicalSpecialistOutput:
    """Technical specialist agent using DSPy.React with technical tools"""
    dspy.context(lm=_GLOBAL_LM)
    
    # Set workflow context for user interaction tools
    set_workflow_context(
        ticket_workflow_id=input_data.ticket_workflow_id,
        ticket_id=input_data.ticket_id,
        agent_type="TECHNICAL_SPECIALIST"
    )
    
    # Create React module with technical tools + user interaction - agent will autonomously determine what tools to use
    tech_react = dspy.ReAct(
        TechnicalSpecialistResponse,
        tools=[
            search_knowledge_base_tool, 
            get_product_specs, 
            check_warranty, 
            create_escalation_ticket, 
            run_diagnostics, 
            check_firmware_updates,
            ask_user_question,  # Allow agent to ask clarifying questions
            validate_user_response
        ]
    )
    
    # Convert customer_profile dict to string for ReAct compatibility
    customer_profile_str = str(input_data.customer_profile) if input_data.customer_profile else "No profile data available"
    
    result = await tech_react.acall(
        issue_description=input_data.issue_description,
        conversation_context=input_data.conversation_context,
        customer_id=input_data.customer_id,
        customer_profile=customer_profile_str
    )

    serialized_history = capture_llm_history()
    
    return TechnicalSpecialistOutput(
        response=result.response,
        confidence=float(result.confidence),
        requires_escalation=result.requires_escalation,
        troubleshooting_steps=result.troubleshooting_steps,  # Now expects str, not list
        estimated_resolution_time=result.estimated_resolution_time,
        llm_history=serialized_history,
        tool_results=getattr(result, 'tool_results', {})
    )