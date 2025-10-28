"""Response Synthesis Activity - Intelligently combine multiple specialist responses"""

from typing import Any, Dict, List

import dspy
from temporalio import activity

from activities.utils import capture_llm_history
from data.interaction_models import SynthesisInput, SynthesisOutput, SpecialistResponse

class ResponseSynthesis(dspy.Signature):
    """Synthesize multiple specialist responses into a coherent, comprehensive customer response"""
    customer_query: str = dspy.InputField(desc="Original customer question/request")
    conversation_context: str = dspy.InputField(desc="Conversation history and context")
    customer_profile: str = dspy.InputField(desc="Customer information")
    specialist_responses: str = dspy.InputField(desc="JSON array of responses from different specialists")
    
    final_response: str = dspy.OutputField(desc="Coherent synthesized response addressing all aspects")
    confidence: float = dspy.OutputField(desc="Overall confidence in the synthesized response")
    information_sources: str = dspy.OutputField(desc="JSON array indicating which specialists contributed what information")
    requires_escalation: bool = dspy.OutputField(desc="Whether any specialist flagged need for escalation")
    synthesis_reasoning: str = dspy.OutputField(desc="Explanation of how responses were combined")

_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")

@activity.defn
async def response_synthesis_activity(input_data: SynthesisInput) -> SynthesisOutput:
    """Synthesize multiple specialist responses using DSPy"""
    dspy.context(lm=_GLOBAL_LM)
    
    # Convert specialist responses to JSON string for DSPy
    import json
    specialist_data = [
        {
            "agent_type": resp.agent_type.value if hasattr(resp.agent_type, 'value') else str(resp.agent_type),
            "response": resp.response,
            "confidence": resp.confidence,
            "requires_escalation": resp.requires_escalation,
            "questions_asked": resp.questions_asked,
            "additional_data": resp.additional_data
        }
        for resp in input_data.specialist_responses
    ]
    
    synthesis_predictor = dspy.Predict(ResponseSynthesis)
    
    result = await synthesis_predictor.acall(
        customer_query=input_data.customer_query,
        conversation_context=input_data.conversation_context,
        customer_profile=str(input_data.customer_profile),
        specialist_responses=json.dumps(specialist_data, indent=2)
    )

    serialized_history = capture_llm_history()
    
    # Parse information sources
    try:
        sources = json.loads(result.information_sources)
    except (json.JSONDecodeError, Exception):
        sources = [f"Specialist {i+1}" for i in range(len(input_data.specialist_responses))]
    
    return SynthesisOutput(
        final_response=str(result.final_response),
        confidence=float(result.confidence),
        information_sources=sources if isinstance(sources, list) else [str(sources)],
        requires_escalation=bool(result.requires_escalation),
        synthesis_reasoning=str(result.synthesis_reasoning),
        llm_history=serialized_history
    )
