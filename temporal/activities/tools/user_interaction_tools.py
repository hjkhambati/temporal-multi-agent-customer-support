"""User Interaction Tools - Allow agents to ask questions and receive responses from customers"""

from typing import Dict, Any, Optional
import os
import uuid
from datetime import timedelta
from temporalio.client import Client
from data.interaction_models import UserQuestion

# Global storage for workflow context (will be set by specialist workflows)
_workflow_context: Dict[str, Any] = {}

def set_workflow_context(ticket_workflow_id: str, ticket_id: str, agent_type: str):
    """Set workflow context for user interaction"""
    _workflow_context['ticket_workflow_id'] = ticket_workflow_id
    _workflow_context['ticket_id'] = ticket_id
    _workflow_context['agent_type'] = agent_type


async def ask_user_question(
    question: str,
    expected_response_type: str = "text",
    timeout_seconds: int = 300
) -> Dict[str, Any]:
    """
    ASYNC tool for agents to ask clarifying questions to the customer.
    
    This tool executes a UserQuestionWorkflow as a child workflow that:
    1. Signals main ticket workflow to display the question
    2. Waits for user response via signal
    3. Returns the answer to the agent
    
    Args:
        question: The question to ask the user
        expected_response_type: Type of expected response (text, number, yes_no, order_id, etc.)
        timeout_seconds: How long to wait for user response
        
    Returns:
        Dict with user's answer or timeout error
        
    Note: This is an ASYNC tool that works with dspy.ReAct.acall()
    According to DSPy docs: "When using dspy.ReAct with tools, calling acall() on the 
    ReAct instance will automatically execute all tools asynchronously using their acall() methods."
    """
    try:
        # Get workflow context
        ticket_workflow_id = _workflow_context.get('ticket_workflow_id', 'unknown')
        ticket_id = _workflow_context.get('ticket_id', 'unknown')
        agent_type = _workflow_context.get('agent_type', 'SYSTEM')
        
        if ticket_workflow_id == 'unknown' or ticket_id == 'unknown':
            return {
                "success": False,
                "error": "Workflow context not set. Cannot ask user question without context."
            }
        
        # Generate unique question workflow ID
        question_workflow_id = f"{ticket_id}-question-{uuid.uuid4()}"
        
        # Connect to Temporal
        temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
        client = await Client.connect(temporal_address)
        
        # Import here to avoid circular dependency
        from workflows.user_question_workflow import UserQuestionWorkflow
        
        # Create UserQuestion input object
        question_input = UserQuestion(
            question=question,
            parent_workflow_id=ticket_workflow_id,
            ticket_id=ticket_id,
            agent_type=agent_type,
            expected_response_type=expected_response_type,
            timeout_seconds=timeout_seconds
        )
        
        # Execute workflow and wait for result
        answer = await client.execute_workflow(
            UserQuestionWorkflow.run,
            question_input,
            id=question_workflow_id,
            task_queue=os.getenv("TASK_QUEUE", "customer-support-task-queue")
        )
        
        return {
            "success": True,
            "data": answer,
            "message": f"User answered: {answer}"
        }
        
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to ask question: {str(e)}"
        }

def get_pending_user_response(question_id: str) -> Dict[str, Any]:
    """
    Check if a user response is available for a given question.
    
    Args:
        question_id: The ID of the question to check
        
    Returns:
        Dict with response if available, or pending status
    """
    try:
        responses = _workflow_context.get('question_responses', {})
        
        if question_id in responses:
            return {
                "success": True,
                "has_response": True,
                "response": responses[question_id]
            }
        else:
            return {
                "success": True,
                "has_response": False,
                "message": "Waiting for user response"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check response: {str(e)}"
        }

def validate_user_response(
    response: str,
    expected_type: str
) -> Dict[str, Any]:
    """
    Validate that user response matches expected type.
    
    Args:
        response: User's response
        expected_type: Expected response type
        
    Returns:
        Dict with validation result
    """
    try:
        if expected_type == "yes_no":
            valid = response.lower() in ['yes', 'no', 'y', 'n']
            return {"valid": valid, "message": "Valid yes/no response" if valid else "Please answer yes or no"}
            
        elif expected_type == "number":
            try:
                float(response)
                return {"valid": True, "message": "Valid number"}
            except ValueError:
                return {"valid": False, "message": "Please provide a numeric value"}
                
        elif expected_type == "order_id":
            # Simple validation - starts with ORD- or is numeric
            valid = response.startswith("ORD-") or response.isdigit()
            return {"valid": valid, "message": "Valid order ID" if valid else "Please provide a valid order ID"}
            
        else:  # text or other types
            valid = len(response.strip()) > 0
            return {"valid": valid, "message": "Valid response" if valid else "Please provide a response"}
            
    except Exception as e:
        return {"valid": False, "message": f"Validation error: {str(e)}"}
