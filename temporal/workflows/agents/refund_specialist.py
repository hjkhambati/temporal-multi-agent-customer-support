"""Refund Specialist Agent Workflow"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, List

with workflow.unsafe.imports_passed_through():
    from activities.refund_activity import refund_specialist_activity
    from data.agent_models import RefundSpecialistInput, RefundSpecialistOutput

@workflow.defn
class RefundSpecialistAgent:
    @workflow.run
    async def run(self, input_data: RefundSpecialistInput) -> RefundSpecialistOutput:
        """Refund specialist workflow that handles refund and return requests"""
        
        # Execute the refund specialist activity with timeout
        result = await workflow.execute_activity(
            refund_specialist_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        workflow.upsert_memo({"llm-history": result.llm_history})
        
        return result