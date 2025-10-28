from datetime import timedelta, datetime
from temporalio import workflow
import asyncio
from typing import Optional

with workflow.unsafe.imports_passed_through():
    from data.base_models import TicketStatus, AgentType, UrgencyLevel, MessageType
    from data.ticket_models import TicketState, ChatMessage, WorkflowPayload
    from data.agent_models import OrchestratorInput, OrchestratorOutput
    from workflows.agents.orchestrator_agent import OrchestratorAgent

@workflow.defn
class TicketWorkflow:
    def __init__(self) -> None:
        self._pending_queries: asyncio.Queue[ChatMessage] = asyncio.Queue()
        self._waiting_for_answer_workflow_id: Optional[str] = None  # Tracks which question workflow is waiting
        self.state: TicketState | None = None

    @workflow.run
    async def run(
        self,
        ticket_details: WorkflowPayload
    ) -> str:
        """Fully agent-driven workflow - no hardcoded business logic"""

        # Initialize ticket state
        self.state = TicketState(
            ticket_id=ticket_details.ticket_id,
            customer_id=ticket_details.customer_id,
            customer_profile=ticket_details.customer_profile,
            status=TicketStatus.OPEN,
            current_intent=None,
            urgency_level=UrgencyLevel.LOW,
            assigned_agent_type=None,
            context={},
            chat_history=[],
            created_at=workflow.now(),
            last_updated=workflow.now(),
        )

        # Add initial customer message
        first_msg = ChatMessage(
            id=str(workflow.uuid4()),
            ticket_id=ticket_details.ticket_id,
            content=ticket_details.initial_message,
            message_type=MessageType.CUSTOMER,
            agent_type=None,
            timestamp=workflow.now(),
        )

        self.state.chat_history.append(first_msg)
        self._pending_queries.put_nowait(first_msg)

        workflow.logger.info(f"Starting agent-driven workflow for ticket {ticket_details.ticket_id}")

        # Main processing loop
        while True:
            await workflow.wait_condition(
                lambda: not self._pending_queries.empty()
                or self.state.status in [TicketStatus.CLOSED, TicketStatus.RESOLVED]
            )

            while not self._pending_queries.empty():
                query = self._pending_queries.get_nowait()
                
                # Process customer messages through orchestrator
                if query.message_type == MessageType.CUSTOMER:
                    await self._process_with_orchestrator(query)
                    
                self.state.last_updated = workflow.now()

            if self.state.status in [TicketStatus.CLOSED, TicketStatus.RESOLVED]:
                return f"Ticket {self.state.ticket_id} completed by agents."

    async def _process_with_orchestrator(self, message: ChatMessage) -> None:
        """
        Enhanced orchestration pipeline using OrchestratorAgent.
        
        Flow:
        1. Create orchestrator input with message, history, profile
        2. Execute OrchestratorAgent (child workflow)
            a. Orchestrator plans execution (DSPy activity)
            b. Orchestrator executes agents with dependencies
            c. Orchestrator synthesizes response (DSPy activity)
        3. Update state with orchestrator results
        4. Handle escalation if needed
        
        All messages visible to user in chat_history!
        """
        
        workflow.logger.info(f"Processing message with orchestrator: '{message.content[:100]}...'")
        
        # Get ticket workflow ID for passing to orchestrator (for agent question routing)
        ticket_workflow_id = workflow.info().workflow_id
        
        # Prepare orchestrator input with comprehensive chat history
        orchestrator_input = OrchestratorInput(
            customer_message=message.content,
            chat_history=[f"[{msg.message_type.value}] {msg.content}" for msg in self.state.chat_history if msg.id != message.id],
            customer_profile=self.state.customer_profile,
            customer_id=self.state.customer_id,
            ticket_id=self.state.ticket_id,
            ticket_workflow_id=ticket_workflow_id,
            available_agents=[
                AgentType.ORDER_SPECIALIST.value,
                AgentType.TECHNICAL_SPECIALIST.value,
                AgentType.REFUND_SPECIALIST.value,
                AgentType.GENERAL_SUPPORT.value,
                AgentType.ESCALATION_MANAGER.value,
                AgentType.MALE_SPECIALIST.value,
                AgentType.FEMALE_SPECIALIST.value,
                AgentType.BILLING.value,
                AgentType.DELIVERY.value,
                AgentType.ALTERATION.value
            ]
        )
        
        # Execute orchestrator as child workflow
        orchestrator_workflow_id = f"{self.state.ticket_id}-orchestrator-{workflow.uuid4()}"
        
        workflow.logger.info(f"Launching orchestrator child workflow: {orchestrator_workflow_id}")
        
        orchestrator_result = await workflow.execute_child_workflow(
            OrchestratorAgent.run,
            orchestrator_input,
            id=orchestrator_workflow_id,
            task_queue="customer-support-task-queue"
        )
        
        # Update state with orchestrator insights
        self.state.status = TicketStatus.IN_PROGRESS
        self.state.context.update({
            "orchestrator_plan": orchestrator_result.execution_plan,
            "orchestrator_confidence": orchestrator_result.confidence,
            "last_orchestrator_execution": workflow.now().isoformat()
        })
        
        # Handle escalation based on synthesis decision (synthesis evaluates all agent findings)
        if orchestrator_result.requires_escalation:
            workflow.logger.info("Orchestrator synthesis determined escalation needed")
            self.state.status = TicketStatus.ESCALATED_TO_HUMAN
            self.state.context.update({
                "escalation_reason": "Orchestrator determined human assistance needed",
                "escalation_time": workflow.now().isoformat()
            })
        
        # Handle followup if orchestrator determined more work needed
        if orchestrator_result.requires_followup and orchestrator_result.followup_plan:
            workflow.logger.info("Orchestrator detected followup needed - could trigger another cycle")
            # For now, just log it. Could implement iterative orchestration here.
            followup_msg = ChatMessage(
                id=str(workflow.uuid4()),
                ticket_id=self.state.ticket_id,
                content=f"🔄 Follow-up may be needed: {orchestrator_result.synthesis_reasoning}",
                message_type=MessageType.SYSTEM,
                agent_type=AgentType.ORCHESTRATOR,
                timestamp=workflow.now()
            )
            self.state.chat_history.append(followup_msg)
        
        workflow.logger.info(f"Orchestrator processing complete: confidence={orchestrator_result.confidence:.2f}")

    @workflow.signal
    def updateTicketStatus(self, status: str) -> None:
        """Update the ticket status via signal."""
        if self.state:
            self.state.status = TicketStatus(status)
            self.state.last_updated = workflow.now()

    @workflow.signal
    async def addMessage(self, msg: dict) -> None:
        """Add a message to chat history and queue it for processing or route to waiting question workflow."""
        if self.state:
            # Convert dict back to ChatMessage object
            chat_message = ChatMessage.from_dict(msg)
            self.state.chat_history.append(chat_message)
            
            # Skip processing for SYSTEM and AI_AGENT messages (orchestrator outputs)
            # These are already processed and just being logged
            if chat_message.message_type in [MessageType.SYSTEM, MessageType.AI_AGENT]:
                workflow.logger.info(f"Received {chat_message.message_type.value} message, skipping processing")
                self.state.last_updated = workflow.now()
                return
            
            # Check if we're waiting for an answer to a question
            if chat_message.message_type == MessageType.CUSTOMER and self._waiting_for_answer_workflow_id:
                # This customer message is the answer to a pending question
                workflow.logger.info(f"Routing customer message as answer to workflow {self._waiting_for_answer_workflow_id}")
                
                try:
                    # Signal the waiting question workflow
                    question_workflow_handle = workflow.get_external_workflow_handle(self._waiting_for_answer_workflow_id)
                    await question_workflow_handle.signal("receive_answer", chat_message.content)
                    
                    # Update question state
                    for q_id, q_data in self.state.pending_questions.items():
                        if q_data.get("workflow_id") == self._waiting_for_answer_workflow_id:
                            q_data["response"] = chat_message.content
                            q_data["responded_at"] = workflow.now().isoformat()
                            q_data["status"] = "answered"
                            break
                    
                    # Clear waiting state
                    self._waiting_for_answer_workflow_id = None
                    
                    # Resume normal status if no more pending questions
                    pending_count = sum(1 for q in self.state.pending_questions.values() if q.get("status") != "answered")
                    if pending_count == 0:
                        self.state.status = TicketStatus.IN_PROGRESS
                    
                    # Don't process this message further - it's an answer to a question
                    workflow.logger.info("Customer answer routed to question workflow, not processing as new query")
                        
                except Exception as e:
                    workflow.logger.error(f"Failed to route answer to workflow {self._waiting_for_answer_workflow_id}: {str(e)}")
                    # On error, clear waiting state but DON'T process as new query
                    # The agent should ask the question again if needed
                    self._waiting_for_answer_workflow_id = None
            else:
                # Normal customer message - process through orchestrator
                self._pending_queries.put_nowait(chat_message)
            
            self.state.last_updated = workflow.now()

    @workflow.signal
    def display_agent_question(self, question_data: dict) -> None:
        """Handle question from UserQuestionWorkflow - display in chat and set waiting state"""
        if self.state:
            question_id = question_data.get("question_id")
            question_workflow_id = question_data.get("workflow_id")
            
            # Store question in state
            self.state.pending_questions[question_id] = question_data
            self.state.status = TicketStatus.WAITING_FOR_CUSTOMER
            
            # Set state: waiting for answer to this specific question workflow
            self._waiting_for_answer_workflow_id = question_workflow_id
            
            # Add to chat history for display in UI
            question_msg = ChatMessage(
                id=str(workflow.uuid4()),
                ticket_id=self.state.ticket_id,
                content=f"{question_data.get('question')}",
                message_type=MessageType.SYSTEM,
                agent_type=question_data.get("agent_type"),
                timestamp=workflow.now(),
                metadata=question_data  # Contains workflow_id for routing responses
            )
            self.state.chat_history.append(question_msg)
            self.state.last_updated = workflow.now()
            
            workflow.logger.info(f"Question {question_id} displayed in chat. Waiting for answer to workflow {question_workflow_id}")

    @workflow.query
    def getState(self) -> dict | None:
        """Return the current state of the ticket as a serializable dict."""
        return self.state.to_dict() if self.state else None
