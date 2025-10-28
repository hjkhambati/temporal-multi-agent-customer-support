"""Billing Agent Workflow"""

from datetime import timedelta
from temporalio import workflow
from typing import Dict, List

with workflow.unsafe.imports_passed_through():
    from activities.billing_activity import billing_activity
    from data.agent_models import BillingInput, BillingOutput

@workflow.defn
class BillingAgent:
    @workflow.run
    async def run(self, input_data: BillingInput) -> BillingOutput:
        """Billing workflow that handles payment processing and invoicing"""
        
        # Execute the billing activity with timeout
        result = await workflow.execute_activity(
            billing_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=workflow.RetryPolicy(maximum_attempts=2)
        )

        workflow.upsert_memo({"llm-history": result.llm_history})
        
        return result
