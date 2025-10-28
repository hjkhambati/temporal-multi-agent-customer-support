"""Escalation Agent Activity"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import EscalationInput, EscalationOutput

class EscalationDecision(dspy.Signature):
    """
    ESCALATION AGENT - Your responsibilities:
    
    1. Analyze conversation history for escalation triggers:
       - Multiple failed resolution attempts (3+)
       - Customer expressing frustration or dissatisfaction
       - Complex issues beyond AI agent capabilities
       - High-value customers (VIP, Platinum tier)
       - Legal, compliance, or sensitive issues
       - Requests explicitly asking for human agent
    
    2. Assess urgency level based on:
       - Customer sentiment (angry, frustrated, neutral, happy)
       - Issue complexity and business impact
       - Time sensitivity of the request
       - Customer tier and relationship value
    
    3. Determine priority level (1-5):
       - 1: Critical (legal, major incident, VIP very upset)
       - 2: High (frustrated customer, order issues)
       - 3: Medium (standard escalation, complex question)
       - 4: Low (minor issue, informational)
       - 5: Very Low (non-urgent follow-up)
    
    4. Create handover summary for human agent with:
       - Issue summary
       - Customer context
       - Actions already taken
       - Current customer sentiment
       - Recommended next steps
    
    CRITICAL: Escalate proactively when AI agents can't resolve.
    Better to escalate early than frustrate customer further.
    High-value customers get priority escalation.
    """
    conversation_history: List[str] = dspy.InputField()
    customer_satisfaction_indicators: List[str] = dspy.InputField()
    failed_resolution_attempts: int = dspy.InputField()
    urgency_level: int = dspy.InputField()
    agent_responses: List[Dict[str, Any]] = dspy.InputField()
    customer_profile: Dict[str, Any] = dspy.InputField()
    
    should_escalate: bool = dspy.OutputField(desc="Whether to escalate to human")
    escalation_reason: str = dspy.OutputField(desc="Reason for escalation")
    priority_level: int = dspy.OutputField(desc="Human agent priority 1-5")
    handover_summary: str = dspy.OutputField(desc="Context summary for human agent")

# Global LM configuration
_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")

@activity.defn
async def escalation_activity(input_data: EscalationInput) -> EscalationOutput:
    """Escalation agent to determine if human intervention is needed"""
    dspy.context(lm=_GLOBAL_LM)
    
    escalation_predictor = dspy.Predict(EscalationDecision)
    
    result = await escalation_predictor.acall(
        conversation_history=input_data.conversation_history,
        customer_satisfaction_indicators=input_data.customer_satisfaction_indicators,
        failed_resolution_attempts=input_data.failed_resolution_attempts,
        urgency_level=input_data.urgency_level,
        agent_responses=input_data.agent_responses,
        customer_profile=input_data.customer_profile
    )

    serialized_history = capture_llm_history()
    
    return EscalationOutput(
        should_escalate=result.should_escalate,
        escalation_reason=result.escalation_reason,
        priority_level=int(result.priority_level),
        handover_summary=result.handover_summary,
        recommended_next_steps=["Transfer to human agent", "Provide detailed context", "Monitor resolution"],
        llm_history=serialized_history
    )