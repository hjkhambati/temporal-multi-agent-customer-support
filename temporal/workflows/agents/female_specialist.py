"""Female Specialist Agent Workflow"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, List

with workflow.unsafe.imports_passed_through():
    from activities.female_specialist_activity import female_specialist_activity
    from data.agent_models import FemaleSpecialistInput, FemaleSpecialistOutput

@workflow.defn
class FemaleSpecialistAgent:
    @workflow.run
    async def run(self, input_data: FemaleSpecialistInput) -> FemaleSpecialistOutput:
        """Female specialist workflow that handles female clothing measurements and purchases"""
        
        # Execute the female specialist activity with timeout
        result = await workflow.execute_activity(
            female_specialist_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        workflow.upsert_memo({"llm-history": result.llm_history})
        
        return result
