"""Technical Specialist Agent Workflow"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, List

with workflow.unsafe.imports_passed_through():
    from activities.technical_activity import technical_specialist_activity
    from data.agent_models import TechnicalSpecialistInput, TechnicalSpecialistOutput

@workflow.defn
class TechnicalSpecialistAgent:
    @workflow.run
    async def run(self, input_data: TechnicalSpecialistInput) -> TechnicalSpecialistOutput:
        """Technical specialist workflow that handles technical support issues"""
        
        # Execute the technical specialist activity with timeout
        result = await workflow.execute_activity(
            technical_specialist_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        workflow.upsert_memo({"llm-history": result.llm_history})
        
        return result