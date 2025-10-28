"""User Question Workflow - Handles asking questions to users and waiting for responses"""

from temporalio import workflow
import asyncio
from datetime import timedelta
from typing import Optional

with workflow.unsafe.imports_passed_through():
    from data.base_models import MessageType, AgentType
    from data.interaction_models import UserQuestion

@workflow.defn
class UserQuestionWorkflow:
    """
    Workflow that:
    1. Signals parent workflow to display question in chat
    2. Waits for user response via signal
    3. Returns the user's answer
    """
    
    def __init__(self) -> None:
        self._user_answer: Optional[str] = None
        self._answer_received = asyncio.Event()
    
    @workflow.run
    async def run(self, input_data: UserQuestion) -> str:
        """
        Ask user a question and wait for response.
        
        Args:
            input_data: UserQuestion object containing all question details
            
        Returns:
            User's answer or timeout message
        """
        
        question_id = workflow.info().workflow_id
        
        # Prepare question data
        question_data = {
            "question_id": question_id,
            "ticket_id": input_data.ticket_id,
            "question": input_data.question,  # Field name matches now
            "expected_response_type": input_data.expected_response_type,
            "agent_type": input_data.agent_type,
            "asked_at": workflow.now().isoformat(),
            "status": "pending",
            "workflow_id": question_id
        }
        
        # Signal parent workflow to display the question
        parent_handle = workflow.get_external_workflow_handle(input_data.parent_workflow_id)
        await parent_handle.signal("display_agent_question", question_data)
        
        workflow.logger.info(f"Question {question_id} sent to parent workflow {input_data.parent_workflow_id}")
        
        # Wait for user response with timeout
        timeout_seconds = input_data.timeout_seconds
        try:
            await asyncio.wait_for(
                self._answer_received.wait(),
                timeout=timeout_seconds
            )
            
            workflow.logger.info(f"Received answer for question {question_id}: {self._user_answer}")
            return self._user_answer or "No response provided"
            
        except asyncio.TimeoutError:
            workflow.logger.warning(f"Question {question_id} timed out after {timeout_seconds} seconds")
            
            # Signal parent about timeout
            await parent_handle.signal("question_timeout", {
                "question_id": question_id,
                "question": input_data.question
            })
            
            return f"[TIMEOUT: User did not respond within {timeout_seconds} seconds]"
    
    @workflow.signal
    def receive_answer(self, answer: str) -> None:
        """Receive answer from user via signal"""
        workflow.logger.info(f"UserQuestionWorkflow received answer: {answer}")
        self._user_answer = answer
        self._answer_received.set()
    
    @workflow.query
    def get_status(self) -> dict:
        """Get current status of the question"""
        return {
            "answered": self._answer_received.is_set(),
            "answer": self._user_answer
        }
