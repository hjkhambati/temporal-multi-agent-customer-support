from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

class TicketStatus(Enum):
    OPEN = "open"
    WAITING_FOR_CUSTOMER = "waiting_for_customer" 
    IN_PROGRESS = "in_progress"
    ESCALATED_TO_HUMAN = "escalated_to_human"
    RESOLVED = "resolved"
    CLOSED = "closed"

class MessageType(Enum):
    CUSTOMER = "customer"
    AI_AGENT = "ai_agent"
    HUMAN_AGENT = "human_agent"
    SYSTEM = "system"

class AgentType(Enum):
    INTENT_CLASSIFIER = "intent_classifier"
    ORDER_SPECIALIST = "order_specialist"
    TECHNICAL_SPECIALIST = "technical_specialist"
    REFUND_SPECIALIST = "refund_specialist"
    ESCALATION_MANAGER = "escalation_manager"
    HUMAN_AGENT = "human_agent"

class IntentType(Enum):
    ORDER_INQUIRY = "order_inquiry"
    TECHNICAL_SUPPORT = "technical_support"
    REFUND_REQUEST = "refund_request"
    BILLING_QUESTION = "billing_question"
    COMPLAINT = "complaint"
    GENERAL_QUESTION = "general_question"

class UrgencyLevel(Enum):
    LOW = "1"
    MEDIUM = "2"
    HIGH = "3"
    CRITICAL = "4"

@dataclass
class ChatMessage:
    id: str
    ticket_id: str
    content: str
    message_type: MessageType
    agent_type: Optional[AgentType]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TicketState:
    ticket_id: str
    customer_id: str
    customer_profile: Dict[str, Any]
    status: TicketStatus
    current_intent: Optional[IntentType]
    urgency_level: UrgencyLevel
    assigned_agent_type: Optional[AgentType]
    context: Dict[str, Any]
    chat_history: List[ChatMessage]
    created_at: datetime
    last_updated: datetime
    escalation_reason: Optional[str] = None
    resolution_summary: Optional[str] = None
    satisfaction_score: Optional[int] = None

@dataclass
class WorkflowPayload:
    ticket_id: str
    customer_id: str
    initial_message: str
    customer_profile: Dict[str, Any]

@dataclass
class IntentAgentInput:
    message: str
    chat_history: List[str]
    customer_profile: Dict[str, Any]

@dataclass
class IntentAgentOutput:
    intent: str  # IntentType value
    urgency: str  # UrgencyLevel value
    key_entities: List[str]
    confidence: float
    context_summary: str