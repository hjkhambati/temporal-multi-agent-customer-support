"""
Activity for querying parent workflow state.

This activity allows child workflows (like OrchestratorAgent) to query
the current state of parent workflows (like TicketWorkflow) to get
up-to-date information, particularly the latest chat_history.
"""

from temporalio import activity
from temporalio.client import Client
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@activity.defn
async def query_parent_workflow_state(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    Query a workflow's current state.
    
    Args:
        workflow_id: The ID of the workflow to query
        
    Returns:
        Dictionary containing the workflow state, or None if query fails
    """
    try:
        # Create Temporal client
        temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
        client = await Client.connect(temporal_address)
        
        # Get workflow handle and query state
        handle = client.get_workflow_handle(workflow_id)
        state_dict = await handle.query("getState")
        
        return state_dict
        
    except Exception as e:
        logger.error(f"Failed to query workflow {workflow_id}: {e}")
        return None
