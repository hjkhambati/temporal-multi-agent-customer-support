"""Data models for user interaction and multi-intent processing"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from data.base_models import AgentType, IntentType

@dataclass
class IntentDetection:
    """Individual intent detection with metadata"""
    intent: IntentType
    confidence: float
    priority: int  # 1 = highest priority
    reasoning: str
    key_entities: List[str] = field(default_factory=list)

@dataclass
class MultiIntentResult:
    """Result from multi-intent classification"""
    detected_intents: List[IntentDetection]
    primary_intent: IntentType
    requires_parallel_processing: bool
    context_summary: str
    satisfaction_indicators: List[str]
    conversation_context: str
    llm_history: str

@dataclass
class UserQuestion:
    """Question asked by an agent to the user"""
    question: str  # The question text
    parent_workflow_id: str  # Parent workflow to signal
    ticket_id: str  # Ticket context
    agent_type: str = "SYSTEM"  # Which agent is asking
    expected_response_type: str = "text"  # "text", "number", "yes_no", "order_id", etc.
    timeout_seconds: int = 300  # How long to wait for answer
    question_id: str = ""  # Will be set to workflow ID
    asked_at: Optional[datetime] = None  # Set by workflow
    status: str = "pending"  # "pending", "answered", "timeout"
    response: Optional[str] = None  # User's answer
    responded_at: Optional[datetime] = None  # When answered

@dataclass
class SpecialistResponse:
    """Response from a specialist agent"""
    agent_type: AgentType
    response: str
    confidence: float
    requires_escalation: bool
    questions_asked: List[str] = field(default_factory=list)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: int = 0
    additional_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SubWorkflowInfo:
    """Information about active sub-workflow"""
    workflow_id: str
    agent_type: AgentType
    intent: IntentType
    status: str  # "running", "waiting_for_user", "completed", "failed"
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[SpecialistResponse] = None

@dataclass
class SynthesisInput:
    """Input for response synthesis agent"""
    specialist_responses: List[SpecialistResponse]
    customer_query: str
    conversation_context: str
    customer_profile: Dict[str, Any]

@dataclass
class SynthesisOutput:
    """Output from response synthesis agent"""
    final_response: str
    confidence: float
    information_sources: List[str]  # Which agents contributed what
    requires_escalation: bool
    synthesis_reasoning: str
    llm_history: str
