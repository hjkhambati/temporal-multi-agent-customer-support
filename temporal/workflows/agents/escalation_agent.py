"""Escalation Agent Workflow"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, List

with workflow.unsafe.imports_passed_through():
    from activities.escalation_activity import escalation_activity
    from data.agent_models import EscalationInput, EscalationOutput

@workflow.defn
class EscalationAgent:
    @workflow.run
    async def run(self, input_data: EscalationInput) -> EscalationOutput:
        """Escalation agent workflow that determines if human intervention is needed"""
        
        # Execute the escalation activity with timeout
        result = await workflow.execute_activity(
            escalation_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        workflow.upsert_memo({"llm-history": result.llm_history})
        
        return result