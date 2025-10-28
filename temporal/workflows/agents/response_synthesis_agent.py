"""Response Synthesis Agent Workflow"""

from temporalio import workflow
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from data.interaction_models import SynthesisInput, SynthesisOutput
    from activities.response_synthesis_activity import response_synthesis_activity

@workflow.defn
class ResponseSynthesisAgent:
    @workflow.run
    async def run(self, synthesis_input: SynthesisInput) -> SynthesisOutput:
        """Synthesize multiple specialist responses into coherent final response"""
        
        result = await workflow.execute_activity(
            response_synthesis_activity,
            synthesis_input,
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        return result
