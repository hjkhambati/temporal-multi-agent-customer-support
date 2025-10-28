from enum import Enum

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
    ORCHESTRATOR = "orchestrator"  # NEW: Coordinates multi-agent execution
    ORDER_SPECIALIST = "order_specialist"
    TECHNICAL_SPECIALIST = "technical_specialist"
    REFUND_SPECIALIST = "refund_specialist"
    GENERAL_SUPPORT = "general_support"
    ESCALATION_MANAGER = "escalation_manager"
    HUMAN_AGENT = "human_agent"
    # Purchase flow agents
    MALE_SPECIALIST = "male_specialist"
    FEMALE_SPECIALIST = "female_specialist"
    BILLING = "billing"
    DELIVERY = "delivery"
    ALTERATION = "alteration"

class IntentType(Enum):
    ORDER_INQUIRY = "order_inquiry"
    TECHNICAL_SUPPORT = "technical_support"
    REFUND_REQUEST = "refund_request"
    BILLING_QUESTION = "billing_question"
    COMPLAINT = "complaint"
    GENERAL_QUESTION = "general_question"
    PURCHASE = "purchase"  # New purchase intent

class UrgencyLevel(Enum):
    LOW = "1"
    MEDIUM = "2"
    HIGH = "3"
    CRITICAL = "4"

class EscalationReason(Enum):
    COMPLEX_ISSUE = "complex_issue"
    CUSTOMER_DISSATISFIED = "customer_dissatisfied"
    MULTIPLE_FAILED_ATTEMPTS = "multiple_failed_attempts"
    VIP_CUSTOMER = "vip_customer"
    POLICY_EXCEPTION_NEEDED = "policy_exception_needed"
    TECHNICAL_LIMITATION = "technical_limitation"

class ExecutionStrategy(Enum):
    """How orchestrator coordinates agent execution"""
    SEQUENTIAL = "sequential"      # Agent A → B → C (dependencies)
    PARALLEL = "parallel"           # A || B || C (independent)
    CONDITIONAL = "conditional"     # If A.result → B else C
    HYBRID = "hybrid"               # Mix of sequential and parallel