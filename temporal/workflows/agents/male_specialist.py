"""Male Specialist Agent Workflow"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, List

with workflow.unsafe.imports_passed_through():
    from activities.male_specialist_activity import male_specialist_activity
    from data.agent_models import MaleSpecialistInput, MaleSpecialistOutput

@workflow.defn
class MaleSpecialistAgent:
    @workflow.run
    async def run(self, input_data: MaleSpecialistInput) -> MaleSpecialistOutput:
        """Male specialist workflow that handles male clothing measurements and purchases"""
        
        # Execute the male specialist activity with timeout
        result = await workflow.execute_activity(
            male_specialist_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        workflow.upsert_memo({"llm-history": result.llm_history})
        
        return result
