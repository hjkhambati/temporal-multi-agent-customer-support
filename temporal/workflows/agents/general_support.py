"""General Support Specialist Agent Workflow"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, List

with workflow.unsafe.imports_passed_through():
    from activities.general_activity import general_support_activity
    from data.agent_models import GeneralSupportInput, GeneralSupportOutput

@workflow.defn
class GeneralSupportAgent:
    @workflow.run
    async def run(self, input_data: GeneralSupportInput) -> GeneralSupportOutput:
        """General support specialist workflow that handles general inquiries"""
        
        # Execute the general support activity with timeout
        result = await workflow.execute_activity(
            general_support_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        workflow.upsert_memo({"llm-history": result.llm_history})
        
        return result