"""Orchestrator Planning and Synthesis Activities - Intelligent Multi-Agent Coordination"""

from typing import Any, Dict, List, Literal
import json
import dspy
import pydantic
from temporalio import activity

from activities.utils import capture_llm_history
from data.agent_models import (
    OrchestratorInput, OrchestratorOutput, 
    ExecutionPlan, ExecutionStep, AgentExecutionResult
)
from data.base_models import AgentType
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# DSPY SIGNATURES
# ============================================================================

class ExecutionStepOutput(pydantic.BaseModel):
    """Single step in execution plan"""
    step: int = pydantic.Field(description="Step number (1, 2, 3...)")
    agent: Literal[
        "order_specialist", "technical_specialist", "refund_specialist", "general_support", 
        "escalation_manager", "male_specialist", "female_specialist", "billing", "delivery", "alteration"
    ] = pydantic.Field(description="Agent type - must be one of the available specialist agents")
    reason: str = pydantic.Field(description="Why this agent is needed")
    depends_on: list[int] = pydantic.Field(default_factory=list, description="Which step numbers must complete first")
    context_refs: list[str] = pydantic.Field(
        default_factory=list,
        description="Step references like ['step_1', 'step_2'] for any steps this agent depends on. CRITICAL: If depends_on=[1], then context_refs=['step_1']"
    )
    priority: int = pydantic.Field(default=1, description="Priority within parallel execution (lower = higher priority)")


class OrchestratorPlanning(dspy.Signature):
    """
    Analyze customer query and create intelligent execution plan for specialist agents.
    Determine which agents to call, in what order, and how to pass context between them.
    
    AVAILABLE SPECIALIST AGENTS AND THEIR PURPOSES:
    
    **POST-PURCHASE AGENTS** (for existing orders and issues):
    - order_specialist: Track EXISTING orders, check shipping status, update delivery addresses, view order history
    - technical_specialist: Troubleshoot product malfunctions, provide setup guides, diagnose technical issues
    - refund_specialist: Process refunds and returns for EXISTING orders, check refund eligibility
    - general_support: Answer general questions, company policies, account issues, FAQs
    
    **PURCHASE FLOW AGENTS** (for NEW clothing purchases):
    - male_specialist: Help customers BUY male clothing (shirts, pants, suits). Collects measurements (chest, waist, shoulder, sleeve, neck, inseam), validates sizes, recommends fit
    - female_specialist: Help customers BUY female clothing (dresses, blouses, skirts). Collects measurements (bust, waist, hip, shoulder, sleeve, dress length), validates sizes, recommends fit
    - billing: Calculate prices, apply discount codes (FIRST10, SAVE20, FLAT50, VIP25), process payments, generate invoices
    - delivery: Schedule shipping, validate addresses, calculate delivery dates (Standard/Express/Overnight), provide tracking
    - alteration: Handle clothing alterations (hemming, taking in, letting out, sleeve/waist adjustments), check feasibility, calculate alteration costs
    
    **PURCHASE vs POST-PURCHASE DISTINCTION**:
    - Keywords "buy", "purchase", "want to get", "looking for", "shop for", "need new" → Use PURCHASE agents (male/female_specialist → billing → delivery)
    - Keywords "order #", "tracking", "where is my", "return", "refund", "broken", "not working" → Use POST-PURCHASE agents (order/technical/refund_specialist)
    
    EXECUTION STRATEGIES:
    - Sequential: Steps must run in order (e.g., male_specialist → billing → delivery for purchase flow)
    - Parallel: Independent agents can run simultaneously (e.g., order_specialist + technical_specialist for different issues)
    - Hybrid: Some steps parallel, some sequential based on dependencies
    
    CRITICAL RULE: If a step depends_on another step, it MUST have that step's reference in context_refs.
    Example: If step 2 depends_on=[1], then step 2 must have context_refs=['step_1']
    """
    customer_message: str = dspy.InputField(desc="The customer's query/request")
    conversation_history: str = dspy.InputField(desc="Previous conversation context")
    customer_profile: dict = dspy.InputField(desc="Customer tier, history, preferences")
    available_agents: list[str] = dspy.InputField(desc="List of available specialist agent types")
    
    steps: list[ExecutionStepOutput] = dspy.OutputField(
        desc="Execution plan steps. MUST populate context_refs=['step_X'] for any step that has depends_on=[X]"
    )
    strategy: Literal["sequential", "parallel", "conditional", "hybrid"] = dspy.OutputField(
        desc="Execution strategy: 'sequential' (agents depend on each other), 'parallel' (independent agents), 'conditional' (if-then logic), or 'hybrid' (mix)"
    )
    complexity_level: Literal["simple", "moderate", "complex", "multi_domain"] = dspy.OutputField(
        desc="Query complexity: 'simple' (1 agent), 'moderate' (2 agents), 'complex' (3+ agents), 'multi_domain' (requires multiple specialist types)"
    )
    estimated_duration: int = dspy.OutputField(
        desc="Estimated seconds to complete all steps (simple: 5-10s, moderate: 10-20s, complex: 20-40s)"
    )
    reasoning: str = dspy.OutputField(
        desc="Detailed explanation of why this execution plan was chosen, what dependencies exist, and what strategy is best"
    )


class FollowupPlanOutput(pydantic.BaseModel):
    """Optional followup execution plan"""
    steps: list[ExecutionStepOutput] = pydantic.Field(description="Followup execution steps")
    strategy: Literal["sequential", "parallel", "conditional", "hybrid"] = pydantic.Field(
        default="sequential",
        description="Execution strategy for followup"
    )
    reasoning: str = pydantic.Field(description="Why followup is needed")


class OrchestratorSynthesis(dspy.Signature):
    """
    Synthesize outputs from multiple agent executions into a SINGLE, cohesive customer response.
    
    CRITICAL RULES:
    1. DO NOT repeat what individual agents said - synthesize into ONE unified response
    2. Combine information from all agents into a natural, flowing conversation
    3. Resolve any conflicts or contradictions between agent responses
    4. If multiple agents said similar things, combine them into one coherent statement
    5. Speak as ONE unified assistant, not as multiple agents
    6. Be empathetic and professional
    7. Decide on escalation based on ALL agent findings (e.g., if any agent can't resolve, escalate)
    
    Example of GOOD synthesis:
    - Agent 1: "Order ORD-123 found for headphones"
    - Agent 2: "Outside 30-day return window, can't process refund"
    - Synthesis: "I've reviewed your order ORD-123 for headphones. Unfortunately, since it's been 395 days 
      since purchase, it falls outside our 30-day return policy. However, given the circumstances, 
      I'm escalating this to a specialist who can review alternative solutions for you."
    
    Example of BAD synthesis (what NOT to do):
    - "The order specialist found your order. The refund specialist says you can't get a refund."
    """
    customer_message: str = dspy.InputField(desc="Original customer query")
    execution_plan: dict = dspy.InputField(desc="Execution plan that was executed")
    agent_results: list[dict] = dspy.InputField(
        desc="List of agent execution results with responses, confidence, timing"
    )
    conversation_context: str = dspy.InputField(desc="Overall conversation context and history")
    
    final_response: str = dspy.OutputField(
        desc="SINGLE unified response that synthesizes ALL agent findings into natural conversation. "
        "Speak as ONE assistant, not multiple agents. Be empathetic and actionable."
    )
    confidence: float = dspy.OutputField(
        desc="Overall confidence in the synthesized response (0.0-1.0). Must be between 0.0 and 1.0"
    )
    information_sources: list[str] = dspy.OutputField(
        desc="Internal tracking of which agents contributed (for debugging, not shown to user)"
    )
    requires_escalation: bool = dspy.OutputField(
        desc="True if ANY agent couldn't fully resolve the issue or if customer needs human assistance"
    )
    requires_followup: bool = dspy.OutputField(
        desc="Whether additional agent execution needed based on findings"
    )
    followup_plan: FollowupPlanOutput | None = dspy.OutputField(
        default=None,
        desc="If followup needed, provide execution plan. Otherwise None."
    )
    synthesis_reasoning: str = dspy.OutputField(
        desc="Internal explanation of how responses were combined and why escalation decision was made"
    )


# ============================================================================
# GLOBAL LM CONFIGURATION
# ============================================================================

_GLOBAL_LM = dspy.LM("gemini/gemini-2.5-flash")


# ============================================================================
# ORCHESTRATOR PLANNING ACTIVITY
# ============================================================================

@activity.defn
async def orchestrator_planning_activity(input_data: OrchestratorInput) -> ExecutionPlan:
    """
    Create intelligent execution plan using DSPy reasoning.
    
    This activity:
    1. Analyzes query complexity
    2. Determines which agents are needed
    3. Identifies dependencies between agents
    4. Creates execution plan with stages
    5. Chooses execution strategy (sequential, parallel, hybrid)
    """
    dspy.context(lm=_GLOBAL_LM)
    
    # Use ChainOfThought for complex reasoning with detailed agent instructions in signature docstring
    planner = dspy.ChainOfThought(OrchestratorPlanning)
    
    # Prepare inputs - pass structured types instead of JSON strings
    conversation_history_str = "\n".join(input_data.chat_history) if input_data.chat_history else "No previous conversation"
    
    activity.logger.info(
        f"Orchestrator planning for: '{input_data.customer_message[:100]}...'"
    )
    
    try:
        result = await planner.acall(
            customer_message=input_data.customer_message,
            conversation_history=conversation_history_str,
            customer_profile=input_data.customer_profile,  # Pass dict directly
            available_agents=input_data.available_agents   # Pass list directly
        )
        
        # DSPy now returns structured Pydantic models directly!
        steps = []
        for step_output in result.steps:
            # Validate agent type
            agent_type = step_output.agent
            try:
                AgentType(agent_type)
            except ValueError:
                activity.logger.warning(f"Invalid agent type '{agent_type}', using general_support")
                agent_type = "general_support"
            
            # CRITICAL: Ensure context_refs is populated for dependent steps
            context_refs = step_output.context_refs
            if step_output.depends_on and not context_refs:
                # Auto-populate context_refs if LLM forgot
                context_refs = [f"step_{dep}" for dep in step_output.depends_on]
                activity.logger.warning(
                    f"Step {step_output.step} depends on {step_output.depends_on} but context_refs was empty. "
                    f"Auto-populated: {context_refs}"
                )
            
            steps.append(
                ExecutionStep(
                    step_number=step_output.step,
                    agent_type=agent_type,
                    reason=step_output.reason,
                    depends_on=step_output.depends_on,
                    context_references=context_refs,
                    priority=step_output.priority
                )
            )
        
        execution_plan = ExecutionPlan(
            steps=steps,
            strategy=result.strategy,
            complexity_level=result.complexity_level,
            estimated_duration_seconds=result.estimated_duration,
            reasoning=result.reasoning
        )
        
        activity.logger.info(
            f"Orchestrator created plan: {execution_plan.complexity_level} "
            f"with {len(execution_plan.steps)} steps using {execution_plan.strategy} strategy"
        )
        activity.logger.info(f"Plan steps: {[(s.step_number, s.agent_type, s.context_references) for s in steps]}")
        
        return execution_plan
        
    except Exception as e:
        activity.logger.error(f"Orchestrator planning failed: {e}")
        # Return fallback plan
        return ExecutionPlan(
            steps=[
                ExecutionStep(
                    step_number=1,
                    agent_type="general_support",
                    reason="Fallback plan due to orchestrator error",
                    depends_on=[],
                    context_references=[],
                    priority=1
                )
            ],
            strategy="sequential",
            complexity_level="simple",
            estimated_duration_seconds=10,
            reasoning="Fallback to simple plan due to error"
        )


# ============================================================================
# ORCHESTRATOR SYNTHESIS ACTIVITY
# ============================================================================

@activity.defn
async def orchestrator_synthesis_activity(
    customer_message: str,
    execution_plan: ExecutionPlan,
    agent_results: List[AgentExecutionResult],
    conversation_context: str
) -> OrchestratorOutput:
    """
    Synthesize agent outputs into coherent response.
    
    This activity:
    1. Combines multiple specialist responses
    2. Resolves any conflicts between agents
    3. Creates natural conversational response
    4. Determines if escalation or followup needed
    5. Provides reasoning for synthesis decisions
    """
    dspy.context(lm=_GLOBAL_LM)
    
    # Use ChainOfThought for thoughtful synthesis
    synthesizer = dspy.ChainOfThought(OrchestratorSynthesis)
    
    # Prepare execution plan as structured dict
    execution_plan_dict = {
        "steps": [
            {
                "step": s.step_number,
                "agent": s.agent_type,
                "reason": s.reason,
                "depends_on": s.depends_on
            }
            for s in execution_plan.steps
        ],
        "strategy": execution_plan.strategy,
        "complexity_level": execution_plan.complexity_level
    }
    
    # Prepare agent results as structured list
    agent_results_list = [
        {
            "step": r.step_number,
            "agent": r.agent_type,
            "response": r.response,
            "confidence": r.confidence,
            "requires_escalation": r.requires_escalation,
            "execution_time_ms": r.execution_time_ms
        }
        for r in agent_results
    ]
    
    activity.logger.info(
        f"Orchestrator synthesizing {len(agent_results)} agent responses"
    )
    
    try:
        result = await synthesizer.acall(
            customer_message=customer_message,
            execution_plan=execution_plan_dict,      # Pass dict directly
            agent_results=agent_results_list,        # Pass list directly
            conversation_context=conversation_context
        )
        
        serialized_history = capture_llm_history()
        
        # DSPy now returns structured data directly!
        sources = result.information_sources if result.information_sources else [f"Agent {i+1}" for i in range(len(agent_results))]
        
        # Parse followup plan if needed (now a Pydantic model!)
        followup_plan = None
        if result.requires_followup and result.followup_plan:
            followup_steps = []
            for step_output in result.followup_plan.steps:
                # Auto-populate context_refs if needed
                context_refs = step_output.context_refs
                if step_output.depends_on and not context_refs:
                    context_refs = [f"step_{dep}" for dep in step_output.depends_on]
                
                followup_steps.append(
                    ExecutionStep(
                        step_number=step_output.step,
                        agent_type=step_output.agent,
                        reason=step_output.reason,
                        depends_on=step_output.depends_on,
                        context_references=context_refs,
                        priority=step_output.priority
                    )
                )
            
            followup_plan = ExecutionPlan(
                steps=followup_steps,
                strategy=result.followup_plan.strategy,
                complexity_level="moderate",
                estimated_duration_seconds=20,
                reasoning=result.followup_plan.reasoning
            )
        
        orchestrator_output = OrchestratorOutput(
            final_response=result.final_response,
            confidence=result.confidence,
            execution_plan=execution_plan,
            agent_results=agent_results,
            synthesis_reasoning=result.synthesis_reasoning,
            requires_escalation=result.requires_escalation,  # Added missing field
            requires_followup=result.requires_followup,
            followup_plan=followup_plan,
            llm_history=serialized_history
        )
        
        activity.logger.info(
            f"Orchestrator synthesis complete: confidence={orchestrator_output.confidence:.2f}, "
            f"requires_followup={orchestrator_output.requires_followup}"
        )
        
        return orchestrator_output
        
    except Exception as e:
        activity.logger.error(f"Orchestrator synthesis failed: {e}")
        # Return fallback synthesis
        combined_response = "\n\n".join([
            f"From {r.agent_type}: {r.response}" 
            for r in agent_results
        ])
        
        return OrchestratorOutput(
            final_response=combined_response,
            confidence=0.5,
            execution_plan=execution_plan,
            agent_results=agent_results,
            synthesis_reasoning="Fallback synthesis due to error",
            requires_escalation=True,  # Escalate on error
            requires_followup=False,
            followup_plan=None,
            llm_history=""
        )
