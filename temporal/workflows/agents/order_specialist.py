"""Order Specialist Agent Workflow"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, List

with workflow.unsafe.imports_passed_through():
    from activities.order_activity import order_specialist_activity
    from data.agent_models import OrderSpecialistInput, OrderSpecialistOutput

@workflow.defn
class OrderSpecialistAgent:
    @workflow.run
    async def run(self, input_data: OrderSpecialistInput) -> OrderSpecialistOutput:
        """Order specialist workflow that handles order-related inquiries"""
        
        # Execute the order specialist activity with timeout
        result = await workflow.execute_activity(
            order_specialist_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        workflow.upsert_memo({"llm-history": result.llm_history})
        
        return result