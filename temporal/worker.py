import asyncio
import sys
import os

from temporalio.client import Client
from temporalio.worker import Worker

from workflows.ticket_workflow import TicketWorkflow
from workflows.agents.orchestrator_agent import OrchestratorAgent
from workflows.agents.order_specialist import OrderSpecialistAgent
from workflows.agents.technical_specialist import TechnicalSpecialistAgent
from workflows.agents.refund_specialist import RefundSpecialistAgent
from workflows.agents.general_support import GeneralSupportAgent
from workflows.agents.escalation_agent import EscalationAgent
from workflows.agents.response_synthesis_agent import ResponseSynthesisAgent
from workflows.user_question_workflow import UserQuestionWorkflow
from workflows.maintenance.auto_close_workflow import TicketAutoCloseWorkflow

from workflows.agents.male_specialist import MaleSpecialistAgent
from workflows.agents.female_specialist import FemaleSpecialistAgent
from workflows.agents.billing import BillingAgent
from workflows.agents.delivery import DeliveryAgent
from workflows.agents.alteration import AlterationAgent


from activities.orchestrator_activity import orchestrator_planning_activity, orchestrator_synthesis_activity
from activities.order_activity import order_specialist_activity
from activities.technical_activity import technical_specialist_activity
from activities.refund_activity import refund_specialist_activity
from activities.general_activity import general_support_activity
from activities.escalation_activity import escalation_activity
from activities.response_synthesis_activity import response_synthesis_activity
from activities.maintenance_activity import auto_close_inactive_tickets_activity

from activities.male_specialist_activity import male_specialist_activity
from activities.female_specialist_activity import female_specialist_activity
from activities.billing_activity import billing_activity
from activities.delivery_activity import delivery_activity
from activities.alteration_activity import alteration_activity

from activities.workflow_query_activity import query_parent_workflow_state

import os
import dspy
from dotenv import load_dotenv
load_dotenv()

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS")
TASK_QUEUE = os.getenv("TASK_QUEUE")

async def main():
    dspy.configure(lm=dspy.LM("gemini/gemini-2.5-flash"))
    client = await Client.connect(TEMPORAL_ADDRESS, namespace="default")
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[
            TicketWorkflow, 
            OrchestratorAgent,
            OrderSpecialistAgent,
            TechnicalSpecialistAgent,
            RefundSpecialistAgent,
            GeneralSupportAgent,
            EscalationAgent,
            ResponseSynthesisAgent,
            UserQuestionWorkflow,
            TicketAutoCloseWorkflow,
            MaleSpecialistAgent,
            FemaleSpecialistAgent,
            BillingAgent,
            DeliveryAgent,
            AlterationAgent
        ],
        activities=[
            orchestrator_planning_activity,
            orchestrator_synthesis_activity,
            order_specialist_activity,
            technical_specialist_activity,
            refund_specialist_activity,
            general_support_activity,
            escalation_activity,
            response_synthesis_activity,
            auto_close_inactive_tickets_activity,
            male_specialist_activity,
            female_specialist_activity,
            billing_activity,
            delivery_activity,
            alteration_activity,
            query_parent_workflow_state
        ],
        max_concurrent_activities=50,
        max_concurrent_workflow_tasks=100
    )
    print("Starting multi-agent customer support worker...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
