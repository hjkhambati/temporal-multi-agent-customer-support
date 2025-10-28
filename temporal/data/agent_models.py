from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# Intent Classifier Models (Legacy - Single Intent)
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
    satisfaction_indicators: List[str]
    conversation_context: str
    llm_history: str

# Multi-Intent Classifier Models (New)
@dataclass
class MultiIntentAgentInput:
    message: str
    chat_history: List[str]
    customer_profile: Dict[str, Any]

@dataclass
class DetectedIntent:
    """Single detected intent with metadata"""
    intent: str  # IntentType value
    confidence: float
    priority: int  # 1 = highest
    reasoning: str
    key_entities: List[str] = field(default_factory=list)

@dataclass
class MultiIntentAgentOutput:
    detected_intents: List[DetectedIntent]
    primary_intent: str  # IntentType value
    urgency: str  # UrgencyLevel value
    requires_parallel_processing: bool
    context_summary: str
    satisfaction_indicators: List[str]
    conversation_context: str
    llm_history: str

# Order Specialist Models
@dataclass
class OrderSpecialistInput:
    customer_message: str
    conversation_context: str
    customer_id: str
    customer_profile: Dict[str, Any]
    ticket_id: str = ""  # For user interaction context
    ticket_workflow_id: str = ""  # Main ticket workflow ID for signaling questions back

@dataclass
class OrderSpecialistOutput:
    response: str
    confidence: float
    requires_escalation: bool
    suggested_actions: str  # Changed from List[str] to str to match signature
    llm_history: str
    tool_results: Dict[str, Any] = None

# Technical Specialist Models  
@dataclass
class TechnicalSpecialistInput:
    issue_description: str
    conversation_context: str
    customer_id: str
    customer_profile: Dict[str, Any]
    ticket_id: str = ""  # For user interaction context
    ticket_workflow_id: str = ""  # Main ticket workflow ID for signaling questions back

@dataclass
class TechnicalSpecialistOutput:
    response: str
    confidence: float  # Added to match signature
    requires_escalation: bool
    troubleshooting_steps: str  # Changed from List[str] to str to match signature
    estimated_resolution_time: str
    llm_history: str
    tool_results: Dict[str, Any] = None

# Refund Specialist Models
@dataclass
class RefundSpecialistInput:
    refund_request: str
    conversation_context: str
    customer_id: str
    customer_profile: Dict[str, Any]
    ticket_id: str = ""  # For user interaction context
    ticket_workflow_id: str = ""  # Main ticket workflow ID for signaling questions back

@dataclass
class RefundSpecialistOutput:
    response: str
    confidence: float  # Added to match signature
    requires_escalation: bool  # Added to match signature
    eligibility_assessment: str
    required_documentation: str  # Changed from List[str] to str to match signature
    processing_timeline: str
    llm_history: str
    tool_results: Dict[str, Any] = None

# General Support Models
@dataclass
class GeneralSupportInput:
    customer_message: str
    conversation_context: str
    customer_id: str
    customer_profile: Dict[str, Any]
    ticket_id: str = ""  # For user interaction context
    ticket_workflow_id: str = ""  # Main ticket workflow ID for signaling questions back

@dataclass
class GeneralSupportOutput:
    response: str
    confidence: float
    requires_escalation: bool
    suggested_actions: str  # Changed from List[str] to str to match signature
    llm_history: str
    tool_results: Dict[str, Any] = None

# Escalation Agent Models
@dataclass
class EscalationInput:
    conversation_history: List[str]
    customer_satisfaction_indicators: List[str]
    failed_resolution_attempts: int
    urgency_level: int
    agent_responses: List[Dict[str, Any]]
    customer_profile: Dict[str, Any]

@dataclass
class EscalationOutput:
    should_escalate: bool
    escalation_reason: str
    priority_level: int
    handover_summary: str
    recommended_next_steps: List[str]
    llm_history: str

# ============================================================================
# ORCHESTRATOR AGENT MODELS (NEW)
# ============================================================================

@dataclass
class ExecutionStep:
    """Single step in orchestrator execution plan"""
    step_number: int
    agent_type: str  # AgentType value (e.g., "order_specialist")
    reason: str  # Why this agent is needed
    depends_on: List[int] = field(default_factory=list)  # Which step numbers must complete first
    inputs: Dict[str, Any] = field(default_factory=dict)  # Input parameters for agent
    context_references: List[str] = field(default_factory=list)  # Keys from execution_context to pass (e.g., ["step_1", "step_2"])
    priority: int = 1  # For ordering within parallel execution (lower = higher priority)

@dataclass
class ExecutionPlan:
    """Complete execution plan from orchestrator"""
    steps: List[ExecutionStep]
    strategy: str  # ExecutionStrategy value (sequential, parallel, conditional, hybrid)
    complexity_level: str  # "simple", "moderate", "complex", "multi_domain"
    estimated_duration_seconds: int
    reasoning: str  # Orchestrator's explanation for this plan

@dataclass
class OrchestratorInput:
    """Input to orchestrator agent"""
    customer_message: str
    chat_history: List[str]
    customer_profile: Dict[str, Any]
    customer_id: str
    ticket_id: str
    ticket_workflow_id: str  # Main ticket workflow ID for real-time signaling
    available_agents: List[str]  # AgentType values that can be used

@dataclass
class AgentExecutionResult:
    """Result from executing a single specialist agent"""
    step_number: int
    agent_type: str  # AgentType value
    response: str
    confidence: float
    requires_escalation: bool
    execution_time_ms: int
    tool_results: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class OrchestratorOutput:
    """Final output from orchestrator"""
    final_response: str
    confidence: float
    execution_plan: ExecutionPlan
    agent_results: List[AgentExecutionResult]
    synthesis_reasoning: str
    requires_escalation: bool  # Whether human assistance is needed
    requires_followup: bool
    followup_plan: Optional[ExecutionPlan] = None
    llm_history: str = ""

# ============================================================================
# PURCHASE FLOW AGENT MODELS (NEW)
# ============================================================================

# Male Specialist Models
@dataclass
class MaleSpecialistInput:
    purchase_request: str
    conversation_context: str
    customer_id: str
    customer_profile: Dict[str, Any]
    ticket_id: str = ""
    ticket_workflow_id: str = ""

@dataclass
class MaleSpecialistOutput:
    response: str
    confidence: float
    requires_escalation: bool
    measurements_collected: bool
    measurements_data: str  # JSON string of measurements
    validation_status: str
    llm_history: str
    tool_results: Dict[str, Any] = None

# Female Specialist Models
@dataclass
class FemaleSpecialistInput:
    purchase_request: str
    conversation_context: str
    customer_id: str
    customer_profile: Dict[str, Any]
    ticket_id: str = ""
    ticket_workflow_id: str = ""

@dataclass
class FemaleSpecialistOutput:
    response: str
    confidence: float
    requires_escalation: bool
    measurements_collected: bool
    measurements_data: str  # JSON string of measurements
    validation_status: str
    llm_history: str
    tool_results: Dict[str, Any] = None

# Billing Agent Models
@dataclass
class BillingInput:
    purchase_request: str
    conversation_context: str
    customer_id: str
    customer_profile: Dict[str, Any]
    ticket_id: str = ""
    ticket_workflow_id: str = ""

@dataclass
class BillingOutput:
    response: str
    confidence: float
    requires_escalation: bool
    billing_complete: bool
    total_amount: float
    payment_status: str
    invoice_details: str
    llm_history: str
    tool_results: Dict[str, Any] = None

# Delivery Agent Models
@dataclass
class DeliveryInput:
    purchase_request: str
    conversation_context: str
    customer_id: str
    customer_profile: Dict[str, Any]
    ticket_id: str = ""
    ticket_workflow_id: str = ""

@dataclass
class DeliveryOutput:
    response: str
    confidence: float
    requires_escalation: bool
    delivery_scheduled: bool
    delivery_date: str
    tracking_number: str
    delivery_address: str
    llm_history: str
    tool_results: Dict[str, Any] = None

# Alteration Agent Models
@dataclass
class AlterationInput:
    purchase_request: str
    conversation_context: str
    customer_id: str
    customer_profile: Dict[str, Any]
    ticket_id: str = ""
    ticket_workflow_id: str = ""

@dataclass
class AlterationOutput:
    response: str
    confidence: float
    requires_escalation: bool
    alteration_needed: bool
    alteration_details: str
    additional_cost: float
    llm_history: str
    tool_results: Dict[str, Any] = None