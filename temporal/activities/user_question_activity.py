"""Activity wrapper for executing user question workflow"""

from temporalio import activity, workflow
from typing import Dict, Any
import uuid

@activity.defn
async def execute_user_question_activity(
    parent_workflow_id: str,
    ticket_id: str,
    question: str,
    expected_response_type: str,
    agent_type: str,
    timeout_seconds: int
) -> str:
    """
    Execute a user question workflow and wait for response.
    
    This activity:
    1. Starts a UserQuestionWorkflow as a child workflow
    2. The child workflow signals the parent to display the question
    3. Waits for the user's response
    4. Returns the answer
    """
    from workflows.user_question_workflow import UserQuestionWorkflow
    
    # Generate unique workflow ID for this question
    question_workflow_id = f"question-{ticket_id}-{uuid.uuid4()}"
    
    # Execute the question workflow
    # Note: This needs to be called from within a workflow context, not directly from activity
    # So we'll need a different approach...
    
    # Return the question data for the workflow to handle
    return question
