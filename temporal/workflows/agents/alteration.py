"""Alteration Agent Workflow"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, List

with workflow.unsafe.imports_passed_through():
    from activities.alteration_activity import alteration_activity
    from data.agent_models import AlterationInput, AlterationOutput

@workflow.defn
class AlterationAgent:
    @workflow.run
    async def run(self, input_data: AlterationInput) -> AlterationOutput:
        """Alteration workflow that handles clothing alteration requests"""
        
        # Execute the alteration activity with timeout
        result = await workflow.execute_activity(
            alteration_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        workflow.upsert_memo({"llm-history": result.llm_history})
        
        return result
