"""Delivery Agent Workflow"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, List

with workflow.unsafe.imports_passed_through():
    from activities.delivery_activity import delivery_activity
    from data.agent_models import DeliveryInput, DeliveryOutput

@workflow.defn
class DeliveryAgent:
    @workflow.run
    async def run(self, input_data: DeliveryInput) -> DeliveryOutput:
        """Delivery workflow that handles shipping and tracking"""
        
        # Execute the delivery activity with timeout
        result = await workflow.execute_activity(
            delivery_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        workflow.upsert_memo({"llm-history": result.llm_history})
        
        return result
