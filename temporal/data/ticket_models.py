from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from .base_models import TicketStatus, MessageType, AgentType, IntentType, UrgencyLevel, EscalationReason

@dataclass
class ChatMessage:
    id: str
    ticket_id: str
    content: str
    message_type: MessageType
    agent_type: Optional[AgentType]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    additional_info: Optional[Dict[str, Any]] = field(default_factory=dict)  # For agent-specific structured data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Handle enum values safely - if already a string, keep it; if enum, get value
        data['message_type'] = self.message_type.value if hasattr(self.message_type, 'value') else self.message_type
        data['agent_type'] = (self.agent_type.value if hasattr(self.agent_type, 'value') else self.agent_type) if self.agent_type else None
        data['timestamp'] = self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else self.timestamp
        # additional_info is already serializable as it's a dict
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary for JSON deserialization"""
        data = data.copy()
        data['message_type'] = MessageType(data['message_type'])
        data['agent_type'] = AgentType(data['agent_type']) if data['agent_type'] else None
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

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
    escalation_reason: Optional[EscalationReason] = None
    resolution_summary: Optional[str] = None
    satisfaction_score: Optional[int] = None
    failed_attempts: int = 0
    escalation_count: int = 0
    
    # Multi-agent processing fields
    processing_mode: str = "sequential"  # "sequential" | "parallel"
    detected_intents: List[str] = field(default_factory=list)  # List of IntentType values
    active_subworkflows: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # workflow_id -> SubWorkflowInfo
    specialist_responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # agent_type -> response data
    pending_questions: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # question_id -> UserQuestion data
    synthesis_complete: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Handle enum values safely - if already a string, keep it; if enum, get value
        data['status'] = self.status.value if hasattr(self.status, 'value') else self.status
        data['current_intent'] = (self.current_intent.value if hasattr(self.current_intent, 'value') else self.current_intent) if self.current_intent else None
        data['urgency_level'] = self.urgency_level.value if hasattr(self.urgency_level, 'value') else self.urgency_level
        data['assigned_agent_type'] = (self.assigned_agent_type.value if hasattr(self.assigned_agent_type, 'value') else self.assigned_agent_type) if self.assigned_agent_type else None
        data['escalation_reason'] = (self.escalation_reason.value if hasattr(self.escalation_reason, 'value') else self.escalation_reason) if self.escalation_reason else None
        data['created_at'] = self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at
        data['last_updated'] = self.last_updated.isoformat() if hasattr(self.last_updated, 'isoformat') else self.last_updated
        data['chat_history'] = [msg.to_dict() for msg in self.chat_history]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TicketState':
        """Create from dictionary for JSON deserialization"""
        data = data.copy()
        data['status'] = TicketStatus(data['status'])
        data['current_intent'] = IntentType(data['current_intent']) if data['current_intent'] else None
        data['urgency_level'] = UrgencyLevel(data['urgency_level'])
        data['assigned_agent_type'] = AgentType(data['assigned_agent_type']) if data['assigned_agent_type'] else None
        data['escalation_reason'] = EscalationReason(data['escalation_reason']) if data['escalation_reason'] else None
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        data['chat_history'] = [ChatMessage.from_dict(msg) for msg in data['chat_history']]
        return cls(**data)

@dataclass
class WorkflowPayload:
    ticket_id: str
    customer_id: str
    initial_message: str
    customer_profile: Dict[str, Any]