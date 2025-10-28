"""Orchestrator Agent - Intelligent Multi-Agent Coordination Workflow"""

from temporalio import workflow
from datetime import timedelta
from typing import Dict, Any, List

with workflow.unsafe.imports_passed_through():
    from data.agent_models import (
        OrchestratorInput, OrchestratorOutput,
        ExecutionPlan, ExecutionStep, AgentExecutionResult,
        OrderSpecialistInput, TechnicalSpecialistInput, 
        RefundSpecialistInput, GeneralSupportInput, EscalationInput,
        MaleSpecialistInput, FemaleSpecialistInput, BillingInput,
        DeliveryInput, AlterationInput
    )
    from data.base_models import AgentType
    from activities.orchestrator_activity import (
        orchestrator_planning_activity,
        orchestrator_synthesis_activity
    )
    from activities.workflow_query_activity import query_parent_workflow_state
    # Import specialist workflows
    from workflows.agents.order_specialist import OrderSpecialistAgent
    from workflows.agents.technical_specialist import TechnicalSpecialistAgent
    from workflows.agents.refund_specialist import RefundSpecialistAgent
    from workflows.agents.general_support import GeneralSupportAgent
    from workflows.agents.escalation_agent import EscalationAgent
    # Purchase flow agents
    from workflows.agents.male_specialist import MaleSpecialistAgent
    from workflows.agents.female_specialist import FemaleSpecialistAgent
    from workflows.agents.billing import BillingAgent
    from workflows.agents.delivery import DeliveryAgent
    from workflows.agents.alteration import AlterationAgent


@workflow.defn
class OrchestratorAgent:
    """
    Orchestrator Agent - Plans, coordinates, and synthesizes multi-agent execution.
    
    Responsibilities:
    1. Analyze query complexity and create execution plan (Planning Activity)
    2. Execute agents based on dependencies (sequential/parallel/hybrid)
    3. Pass context between dependent agents (context accumulation)
    4. Synthesize outputs into coherent response (Synthesis Activity)
    5. Determine if followup execution needed
    
    Flow:
        Customer Message 
        → Planning Activity (DSPy creates ExecutionPlan)
        → Execute agents in stages (based on dependencies)
        → Synthesis Activity (DSPy combines outputs)
        → Final response
    """
    
    def __init__(self):
        # Registry mapping agent types to workflow classes
        self.agent_registry = {
            AgentType.ORDER_SPECIALIST: OrderSpecialistAgent,
            AgentType.TECHNICAL_SPECIALIST: TechnicalSpecialistAgent,
            AgentType.REFUND_SPECIALIST: RefundSpecialistAgent,
            AgentType.GENERAL_SUPPORT: GeneralSupportAgent,
            AgentType.ESCALATION_MANAGER: EscalationAgent,
            AgentType.MALE_SPECIALIST: MaleSpecialistAgent,
            AgentType.FEMALE_SPECIALIST: FemaleSpecialistAgent,
            AgentType.BILLING: BillingAgent,
            AgentType.DELIVERY: DeliveryAgent,
            AgentType.ALTERATION: AlterationAgent,
        }
    
    @workflow.run
    async def run(self, input_data: OrchestratorInput) -> OrchestratorOutput:
        """
        Main orchestration flow: Plan → Execute → Synthesize
        
        Args:
            input_data: OrchestratorInput with customer message, history, profile
            
        Returns:
            OrchestratorOutput with final response and execution details
        """
        
        workflow.logger.info(
            f"Orchestrator started for ticket {input_data.ticket_id}"
        )
        
        # ====================================================================
        # PHASE 1: PLANNING
        # ====================================================================
        execution_plan = await self._create_execution_plan(input_data)
        
        workflow.logger.info(
            f"Orchestrator created plan: {execution_plan.complexity_level} "
            f"with {len(execution_plan.steps)} steps using {execution_plan.strategy} strategy"
        )
        workflow.logger.info(f"Plan reasoning: {execution_plan.reasoning}")
        
        # Signal plan to parent ticket workflow for real-time visibility
        await self._signal_plan_to_parent(input_data, execution_plan)
        
        # ====================================================================
        # PHASE 2: EXECUTION
        # ====================================================================
        agent_results = await self._execute_plan(execution_plan, input_data)
        
        workflow.logger.info(
            f"Orchestrator completed {len(agent_results)} agent executions"
        )
        
        # ====================================================================
        # PHASE 3: SYNTHESIS
        # ====================================================================
        conversation_context = "\n".join(input_data.chat_history) if input_data.chat_history else ""
        orchestrator_output = await self._synthesize_response(
            input_data.customer_message,
            execution_plan,
            agent_results,
            conversation_context
        )
        
        workflow.logger.info(
            f"Orchestrator synthesis complete: confidence={orchestrator_output.confidence:.2f}"
        )
        
        # Signal final synthesized response to parent ticket workflow
        await self._signal_final_response_to_parent(input_data, orchestrator_output)
        
        return orchestrator_output
    
    async def _create_execution_plan(self, input_data: OrchestratorInput) -> ExecutionPlan:
        """
        Phase 1: Create intelligent execution plan using DSPy reasoning.
        
        Calls orchestrator_planning_activity which uses DSPy to:
        - Analyze query complexity
        - Determine which agents needed
        - Identify dependencies
        - Choose execution strategy
        """
        execution_plan = await workflow.execute_activity(
            orchestrator_planning_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=2),
        )
        return execution_plan
    
    async def _execute_plan(
        self, 
        execution_plan: ExecutionPlan, 
        input_data: OrchestratorInput
    ) -> List[AgentExecutionResult]:
        """
        Phase 2: Execute agents based on dependency graph.
        
        Strategy:
        - Group steps by dependency level into stages
        - Execute stages sequentially (stage 1, then stage 2, etc.)
        - Within each stage, execute agents in parallel
        - Pass execution_context between stages for context accumulation
        
        Example:
            Stage 1: [OrderSpecialist] 
            → execution_context["step_1"] = order details
            Stage 2: [TechnicalSpecialist] (receives step_1 context)
            → execution_context["step_2"] = technical assessment
            Stage 3: [RefundSpecialist] (receives step_1 + step_2 context)
        """
        
        # Group steps by dependencies into stages
        stages = self._group_by_dependencies(execution_plan.steps)
        
        agent_results = []
        execution_context = {}  # Shared context accumulator
        
        workflow.logger.info(f"Orchestrator executing {len(stages)} stages")
        
        # Execute stages sequentially
        for stage_number, stage_steps in enumerate(stages, 1):
            workflow.logger.info(
                f"Orchestrator executing stage {stage_number}/{len(stages)} "
                f"with {len(stage_steps)} agents: {[s.agent_type for s in stage_steps]}"
            )
            
            # Within each stage, execute agents in parallel
            stage_tasks = []
            for step in stage_steps:
                task = self._execute_single_agent(
                    step,
                    execution_context,
                    input_data,
                    execution_plan  # Pass execution plan to inform agents of downstream steps
                )
                stage_tasks.append((step, task))
            
            # Await all agents in this stage
            for step, task in stage_tasks:
                try:
                    result = await task
                    agent_results.append(result)
                    
                    # Add result to execution context for next stage
                    execution_context[f"step_{step.step_number}"] = {
                        "agent": step.agent_type,
                        "response": result.response,
                        "confidence": result.confidence,
                        "tool_results": result.tool_results,
                        "requires_escalation": result.requires_escalation,
                        "full_output": result.metadata.get("full_specialist_output", {}),  # Pass full output to next agents
                        "additional_info": self._extract_additional_info(result)  # Extract formatted additional_info
                    }
                    
                    workflow.logger.info(
                        f"Step {step.step_number} ({step.agent_type}) completed: "
                        f"confidence={result.confidence:.2f}, "
                        f"time={result.execution_time_ms}ms"
                    )
                    
                    # Signal intermediate agent result to parent for real-time visibility
                    await self._signal_agent_result_to_parent(input_data, result)
                    
                except Exception as e:
                    workflow.logger.error(
                        f"Step {step.step_number} ({step.agent_type}) failed: {e}"
                    )
                    # Create error result but continue with other agents
                    error_result = AgentExecutionResult(
                        step_number=step.step_number,
                        agent_type=step.agent_type,
                        response=f"Agent execution failed: {str(e)}",
                        confidence=0.0,
                        requires_escalation=True,
                        execution_time_ms=0,
                        tool_results={},
                        metadata={"error": str(e)}
                    )
                    agent_results.append(error_result)
        
        return agent_results
    
    async def _execute_single_agent(
        self,
        step: ExecutionStep,
        execution_context: Dict[str, Any],
        input_data: OrchestratorInput,
        execution_plan: ExecutionPlan
    ) -> AgentExecutionResult:
        """
        Execute a single specialist agent with context from dependencies.
        
        Process:
        1. Prepare specialist input with context from dependencies
        2. Get workflow class for this agent type
        3. Execute as child workflow
        4. Convert result to AgentExecutionResult
        
        Args:
            step: ExecutionStep with agent info and dependencies
            execution_context: Dict with outputs from previous stages
            input_data: Original orchestrator input
            
        Returns:
            AgentExecutionResult with response and metadata
        """
        
        start_time = workflow.now()
        
        # Prepare agent-specific input with context from dependencies
        specialist_input = await self._prepare_specialist_input(
            step,
            execution_context,
            input_data,
            execution_plan
        )
        
        # Get workflow class for this agent type
        agent_type_enum = AgentType(step.agent_type)
        workflow_class = self.agent_registry.get(agent_type_enum)
        
        if not workflow_class:
            raise ValueError(f"No workflow found for agent type: {step.agent_type}")
        
        # Execute as child workflow
        workflow_id = f"{input_data.ticket_id}-{step.agent_type}-step{step.step_number}"
        
        workflow.logger.info(
            f"Executing {step.agent_type} (step {step.step_number}): {step.reason}"
        )
        
        specialist_result = await workflow.execute_child_workflow(
            workflow_class.run,
            specialist_input,
            id=workflow_id,
            task_queue="customer-support-task-queue"
        )
        
        execution_time = (workflow.now() - start_time).total_seconds() * 1000
        
        # Extract all fields from specialist output to preserve full context
        specialist_output_dict = {}
        for field_name in dir(specialist_result):
            if not field_name.startswith('_'):
                try:
                    specialist_output_dict[field_name] = getattr(specialist_result, field_name)
                except:
                    pass
        return AgentExecutionResult(
            step_number=step.step_number,
            agent_type=step.agent_type,
            response=specialist_result.response,
            confidence=specialist_result.confidence,
            requires_escalation=specialist_result.requires_escalation,
            execution_time_ms=int(execution_time),
            tool_results=getattr(specialist_result, 'tool_results', {}),
            metadata={
                "reason": step.reason,
                "dependencies": step.depends_on,
                "llm_history": specialist_result.llm_history,
                "full_specialist_output": specialist_output_dict
            }
        )
    
    async def _prepare_specialist_input(
        self,
        step: ExecutionStep,
        execution_context: Dict[str, Any],
        input_data: OrchestratorInput,
        execution_plan: ExecutionPlan
    ):
        """
        Prepare input for specialist with context from dependencies.
        
        This is where context passing happens!
        
        Process:
        1. Start with original customer message
        2. For each context reference (dependency), add that agent's output
        3. Create conversation_context that includes all relevant info
        4. Map to specialist-specific input type
        
        Example:
            Step 3 depends on Steps 1 and 2:
            conversation_context = 
                "Customer: {original message}
                
                [Info from order_specialist]: Order ORD123 verified...
                
                [Info from technical_specialist]: Issue is DOA..."
        """
        
        # Build comprehensive conversation context with:
        # 1. LATEST chat history from parent workflow (includes all agent Q&A)
        # 2. Current customer message
        # 3. Outputs from dependent agents
        
        conversation_parts = []
        
        # CRITICAL FIX: Get CURRENT chat history from parent workflow
        # This ensures we include all conversation turns, including agent Q&A
        current_chat_history = input_data.chat_history  # Default fallback
        
        if input_data.ticket_workflow_id:
            try:
                # Query parent workflow for fresh state
                parent_state = await workflow.execute_activity(
                    query_parent_workflow_state,
                    args=[input_data.ticket_workflow_id],
                    start_to_close_timeout=timedelta(seconds=30)
                )
                # Extract and format chat history from parent state
                if parent_state and "chat_history" in parent_state:
                    # Format: "[message_type] content" with additional_info if present
                    current_chat_history = []
                    for msg in parent_state["chat_history"]:
                        formatted_msg = f"[{msg['message_type']}] {msg['content']}"
                        
                        # Include additional_info if present
                        if msg.get('additional_info'):
                            info_parts = []
                            for key, value in msg['additional_info'].items():
                                formatted_key = key.replace('_', ' ').title()
                                info_parts.append(f"  • {formatted_key}: {value}")
                            if info_parts:
                                formatted_msg += "\n" + "\n".join(info_parts)
                        
                        current_chat_history.append(formatted_msg)
                    
                    workflow.logger.info(f"Retrieved {len(current_chat_history)} messages from parent workflow")
            except Exception as e:
                workflow.logger.warning(f"Failed to query parent workflow state: {e}. Using initial chat history.")
        
        # Add chat history if available
        if current_chat_history:
            conversation_parts.append("Previous conversation:")
            conversation_parts.extend(current_chat_history)
            conversation_parts.append("\n---\n")
        
        # Add current message
        conversation_parts.append(f"Current customer message: {input_data.customer_message}")
        
        # CRITICAL: Inform agent about downstream agents (prevents unnecessary escalation)
        next_agents = []
        for other_step in execution_plan.steps:
            if step.step_number in other_step.depends_on:
                next_agents.append(other_step.agent_type)
        
        if next_agents:
            conversation_parts.append(
                f"\n⚠️ WORKFLOW CONTEXT: After you complete your task, these agents will handle next steps: {', '.join(next_agents)}. "
                f"Focus ONLY on your specific responsibility. DO NOT escalate or claim inability if your task is achievable. "
                f"Example: If you're order_specialist and refund_specialist is next, just gather order details - don't try to process refunds."
            )
        
        # Add context from dependent agents (this is the key for dependency passing!)
        workflow.logger.info(
            f"Context references for {step.agent_type}: {step.context_references}"
        )
        workflow.logger.info(
            f"Available in execution_context: {list(execution_context.keys())}"
        )
        
        if step.context_references:
            conversation_parts.append("\n--- Information from previous agents ---")
            for context_ref in step.context_references:
                workflow.logger.info(f"Looking for context_ref: {context_ref}")
                if context_ref in execution_context:
                    dep_data = execution_context[context_ref]
                    conversation_parts.append(
                        f"\n[{dep_data['agent']} findings]:\n{dep_data['response']}"
                    )
                    
                    # Include additional_info (formatted fields ready for display)
                    additional_info = dep_data.get('additional_info', {})
                    if additional_info:
                        info_parts = []
                        for key, value in additional_info.items():
                            formatted_key = key.replace('_', ' ').title()
                            info_parts.append(f"  • {formatted_key}: {value}")
                        if info_parts:
                            conversation_parts.append("\n".join(info_parts))
                    
                    # Include structured data from previous agent if available (fallback)
                    full_output = dep_data.get('full_output', {})
                    if full_output:
                        structured_info = []
                        
                        # Order/General Support: suggested_actions
                        if 'suggested_actions' in full_output and full_output['suggested_actions']:
                            structured_info.append(f"  • Suggested Actions: {full_output['suggested_actions']}")
                        
                        # Technical: troubleshooting_steps, estimated_resolution_time
                        if 'troubleshooting_steps' in full_output and full_output['troubleshooting_steps']:
                            structured_info.append(f"  • Troubleshooting Steps: {full_output['troubleshooting_steps']}")
                        if 'estimated_resolution_time' in full_output and full_output['estimated_resolution_time']:
                            structured_info.append(f"  • Estimated Time: {full_output['estimated_resolution_time']}")
                        
                        # Refund: eligibility_assessment, required_documentation, processing_timeline
                        if 'eligibility_assessment' in full_output and full_output['eligibility_assessment']:
                            structured_info.append(f"  • Eligibility: {full_output['eligibility_assessment']}")
                        if 'required_documentation' in full_output and full_output['required_documentation']:
                            structured_info.append(f"  • Required Docs: {full_output['required_documentation']}")
                        if 'processing_timeline' in full_output and full_output['processing_timeline']:
                            structured_info.append(f"  • Timeline: {full_output['processing_timeline']}")
                        
                        # Male/Female Specialist: measurements_collected, measurements_data, validation_status
                        if 'measurements_collected' in full_output:
                            structured_info.append(f"  • Measurements Collected: {full_output['measurements_collected']}")
                        if 'measurements_data' in full_output and full_output['measurements_data']:
                            structured_info.append(f"  • Measurements: {full_output['measurements_data']}")
                        if 'validation_status' in full_output and full_output['validation_status']:
                            structured_info.append(f"  • Validation: {full_output['validation_status']}")
                        
                        # Billing: billing_complete, total_amount, payment_status, invoice_details
                        if 'billing_complete' in full_output:
                            structured_info.append(f"  • Billing Complete: {full_output['billing_complete']}")
                        if 'total_amount' in full_output:
                            structured_info.append(f"  • Total Amount: ${full_output['total_amount']}")
                        if 'payment_status' in full_output and full_output['payment_status']:
                            structured_info.append(f"  • Payment: {full_output['payment_status']}")
                        if 'invoice_details' in full_output and full_output['invoice_details']:
                            structured_info.append(f"  • Invoice: {full_output['invoice_details']}")
                        
                        # Delivery: delivery_scheduled, delivery_date, tracking_number, delivery_address
                        if 'delivery_scheduled' in full_output:
                            structured_info.append(f"  • Delivery Scheduled: {full_output['delivery_scheduled']}")
                        if 'delivery_date' in full_output and full_output['delivery_date']:
                            structured_info.append(f"  • Delivery Date: {full_output['delivery_date']}")
                        if 'tracking_number' in full_output and full_output['tracking_number']:
                            structured_info.append(f"  • Tracking: {full_output['tracking_number']}")
                        if 'delivery_address' in full_output and full_output['delivery_address']:
                            structured_info.append(f"  • Address: {full_output['delivery_address']}")
                        
                        # Alteration: alteration_needed, alteration_details, additional_cost
                        if 'alteration_needed' in full_output:
                            structured_info.append(f"  • Alteration Needed: {full_output['alteration_needed']}")
                        if 'alteration_details' in full_output and full_output['alteration_details']:
                            structured_info.append(f"  • Alterations: {full_output['alteration_details']}")
                        if 'additional_cost' in full_output:
                            structured_info.append(f"  • Additional Cost: ${full_output['additional_cost']}")
                        
                        if structured_info:
                            conversation_parts.append("\n".join(structured_info))
                    
                    # Include tool results for additional context
                    if dep_data.get('tool_results'):
                        conversation_parts.append(f"  • Tool Data: {dep_data['tool_results']}")
                    
                    workflow.logger.info(f"Added context from {dep_data['agent']}")
                else:
                    workflow.logger.warning(
                        f"Context reference {context_ref} not found in execution_context!"
                    )
            conversation_parts.append("--- End of previous agent information ---\n")
        else:
            workflow.logger.info(f"No context_references for {step.agent_type}")
        
        conversation_context = "\n".join(conversation_parts)
        
        # Get customer ID and ticket workflow ID from input (now passed from TicketWorkflow)
        customer_id = input_data.customer_id
        ticket_workflow_id = input_data.ticket_workflow_id
        
        # Map to specialist-specific input type
        if step.agent_type == AgentType.ORDER_SPECIALIST.value:
            return OrderSpecialistInput(
                customer_message=input_data.customer_message,
                conversation_context=conversation_context,
                customer_id=customer_id,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
        elif step.agent_type == AgentType.TECHNICAL_SPECIALIST.value:
            return TechnicalSpecialistInput(
                issue_description=input_data.customer_message,
                conversation_context=conversation_context,
                customer_id=customer_id,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
        elif step.agent_type == AgentType.REFUND_SPECIALIST.value:
            return RefundSpecialistInput(
                refund_request=input_data.customer_message,
                conversation_context=conversation_context,
                customer_id=customer_id,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
        elif step.agent_type == AgentType.GENERAL_SUPPORT.value:
            return GeneralSupportInput(
                customer_query=input_data.customer_message,
                conversation_context=conversation_context,
                customer_id=customer_id,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
        elif step.agent_type == AgentType.ESCALATION_MANAGER.value:
            return EscalationInput(
                ticket_context=conversation_context,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
        # Purchase flow agents
        elif step.agent_type == AgentType.MALE_SPECIALIST.value:
            return MaleSpecialistInput(
                purchase_request=input_data.customer_message,
                conversation_context=conversation_context,
                customer_id=customer_id,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
        elif step.agent_type == AgentType.FEMALE_SPECIALIST.value:
            return FemaleSpecialistInput(
                purchase_request=input_data.customer_message,
                conversation_context=conversation_context,
                customer_id=customer_id,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
        elif step.agent_type == AgentType.BILLING.value:
            return BillingInput(
                purchase_request=input_data.customer_message,
                conversation_context=conversation_context,
                customer_id=customer_id,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
        elif step.agent_type == AgentType.DELIVERY.value:
            return DeliveryInput(
                purchase_request=input_data.customer_message,
                conversation_context=conversation_context,
                customer_id=customer_id,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
        elif step.agent_type == AgentType.ALTERATION.value:
            return AlterationInput(
                purchase_request=input_data.customer_message,
                conversation_context=conversation_context,
                customer_id=customer_id,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
        else:
            # Fallback to general support
            return GeneralSupportInput(
                customer_query=input_data.customer_message,
                conversation_context=conversation_context,
                customer_id=customer_id,
                customer_profile=input_data.customer_profile,
                ticket_id=input_data.ticket_id,
                ticket_workflow_id=ticket_workflow_id
            )
    
    def _group_by_dependencies(self, steps: List[ExecutionStep]) -> List[List[ExecutionStep]]:
        """
        Group execution steps into stages based on dependencies.
        
        Algorithm:
        1. Start with steps that have no dependencies (stage 1)
        2. Find steps whose dependencies are all in completed stages (stage 2)
        3. Repeat until all steps are assigned to stages
        
        Returns: List of stages, where each stage contains steps that can execute in parallel.
        Steps within a stage have no dependencies on each other.
        
        Example:
            Steps: [1: [], 2: [1], 3: [1], 4: [2,3]]
            Stages: [[1], [2,3], [4]]
                    Stage 1: Step 1 (no deps)
                    Stage 2: Steps 2,3 (both depend only on 1, can run parallel)
                    Stage 3: Step 4 (depends on 2,3)
        """
        stages = []
        remaining = steps.copy()
        completed_steps = set()
        
        max_iterations = len(steps) + 1  # Prevent infinite loop
        iteration = 0
        
        while remaining and iteration < max_iterations:
            iteration += 1
            
            # Find steps with no pending dependencies
            current_stage = []
            for step in remaining[:]:
                if all(dep in completed_steps for dep in step.depends_on):
                    current_stage.append(step)
                    remaining.remove(step)
                    completed_steps.add(step.step_number)
            
            if current_stage:
                # Sort by priority within stage (lower priority number = higher priority)
                current_stage.sort(key=lambda s: s.priority)
                stages.append(current_stage)
            else:
                # Circular dependency or error - log and add remaining as final stage
                if remaining:
                    workflow.logger.error(
                        f"Circular dependency detected in remaining steps: "
                        f"{[s.step_number for s in remaining]}"
                    )
                    # Add remaining as final stage to prevent infinite loop
                    stages.append(remaining)
                break
        
        return stages
    
    async def _synthesize_response(
        self,
        customer_message: str,
        execution_plan: ExecutionPlan,
        agent_results: List[AgentExecutionResult],
        conversation_context: str
    ) -> OrchestratorOutput:
        """
        Phase 3: Synthesize agent outputs into coherent response.
        
        Calls orchestrator_synthesis_activity which uses DSPy to:
        - Combine multiple specialist responses
        - Resolve any conflicts
        - Create natural conversational response
        - Determine if escalation/followup needed
        """
        
        orchestrator_output = await workflow.execute_activity(
            orchestrator_synthesis_activity,
            args=[customer_message, execution_plan, agent_results, conversation_context],
            start_to_close_timeout=timedelta(minutes=2),
        )
        
        return orchestrator_output
    
    def _extract_additional_info(self, agent_result: AgentExecutionResult) -> Dict[str, Any]:
        """Extract additional_info from agent result for context passing"""
        full_output = agent_result.metadata.get("full_specialist_output", {})
        additional_info = {}
        
        # Order Specialist - actual fields: suggested_actions
        if agent_result.agent_type == AgentType.ORDER_SPECIALIST.value:
            if "suggested_actions" in full_output and full_output["suggested_actions"]:
                additional_info["suggested_actions"] = full_output["suggested_actions"]
        
        # Technical Specialist - actual fields: troubleshooting_steps, estimated_resolution_time
        elif agent_result.agent_type == AgentType.TECHNICAL_SPECIALIST.value:
            if "troubleshooting_steps" in full_output and full_output["troubleshooting_steps"]:
                additional_info["troubleshooting_steps"] = full_output["troubleshooting_steps"]
            if "estimated_resolution_time" in full_output and full_output["estimated_resolution_time"]:
                additional_info["estimated_resolution_time"] = full_output["estimated_resolution_time"]
        
        # Refund Specialist - actual fields: eligibility_assessment, required_documentation, processing_timeline
        elif agent_result.agent_type == AgentType.REFUND_SPECIALIST.value:
            if "eligibility_assessment" in full_output and full_output["eligibility_assessment"]:
                additional_info["eligibility_assessment"] = full_output["eligibility_assessment"]
            if "required_documentation" in full_output and full_output["required_documentation"]:
                additional_info["required_documentation"] = full_output["required_documentation"]
            if "processing_timeline" in full_output and full_output["processing_timeline"]:
                additional_info["processing_timeline"] = full_output["processing_timeline"]
        
        # General Support - actual fields: suggested_actions
        elif agent_result.agent_type == AgentType.GENERAL_SUPPORT.value:
            if "suggested_actions" in full_output and full_output["suggested_actions"]:
                additional_info["suggested_actions"] = full_output["suggested_actions"]
        
        # Male/Female Specialist - actual fields: measurements_collected, measurements_data, validation_status
        elif agent_result.agent_type in [AgentType.MALE_SPECIALIST.value, AgentType.FEMALE_SPECIALIST.value]:
            if "measurements_collected" in full_output:
                additional_info["measurements_collected"] = full_output["measurements_collected"]
            if "measurements_data" in full_output and full_output["measurements_data"]:
                additional_info["measurements_data"] = full_output["measurements_data"]
            if "validation_status" in full_output and full_output["validation_status"]:
                additional_info["validation_status"] = full_output["validation_status"]
        
        # Billing - actual fields: billing_complete, total_amount, payment_status, invoice_details
        elif agent_result.agent_type == AgentType.BILLING.value:
            if "billing_complete" in full_output:
                additional_info["billing_complete"] = full_output["billing_complete"]
            if "total_amount" in full_output:
                additional_info["total_amount"] = full_output["total_amount"]
            if "payment_status" in full_output and full_output["payment_status"]:
                additional_info["payment_status"] = full_output["payment_status"]
            if "invoice_details" in full_output and full_output["invoice_details"]:
                additional_info["invoice_details"] = full_output["invoice_details"]
        
        # Delivery - actual fields: delivery_scheduled, delivery_date, tracking_number, delivery_address
        elif agent_result.agent_type == AgentType.DELIVERY.value:
            if "delivery_scheduled" in full_output:
                additional_info["delivery_scheduled"] = full_output["delivery_scheduled"]
            if "delivery_date" in full_output and full_output["delivery_date"]:
                additional_info["delivery_date"] = full_output["delivery_date"]
            if "tracking_number" in full_output and full_output["tracking_number"]:
                additional_info["tracking_number"] = full_output["tracking_number"]
            if "delivery_address" in full_output and full_output["delivery_address"]:
                additional_info["delivery_address"] = full_output["delivery_address"]
        
        # Alteration - actual fields: alteration_needed, alteration_details, additional_cost
        elif agent_result.agent_type == AgentType.ALTERATION.value:
            if "alteration_needed" in full_output:
                additional_info["alteration_needed"] = full_output["alteration_needed"]
            if "alteration_details" in full_output and full_output["alteration_details"]:
                additional_info["alteration_details"] = full_output["alteration_details"]
            if "additional_cost" in full_output:
                additional_info["additional_cost"] = full_output["additional_cost"]
        
        return additional_info
    
    async def _signal_plan_to_parent(
        self,
        input_data: OrchestratorInput,
        execution_plan: ExecutionPlan
    ) -> None:
        """Signal execution plan to parent ticket workflow for immediate visibility"""
        from data.ticket_models import ChatMessage
        from data.base_models import MessageType, AgentType as AT
        
        plan_summary = (
            f"🤖 Orchestrator Plan:\n"
            f"• Complexity: {execution_plan.complexity_level}\n"
            f"• Strategy: {execution_plan.strategy}\n"
            f"• Agents: {', '.join([s.agent_type for s in execution_plan.steps])}\n"
            f"• Reasoning: {execution_plan.reasoning}"
        )
        
        plan_message = ChatMessage(
            id=str(workflow.uuid4()),
            ticket_id=input_data.ticket_id,
            content=plan_summary,
            message_type=MessageType.SYSTEM,
            agent_type=AT.ORCHESTRATOR,
            timestamp=workflow.now(),
            metadata={
                "execution_plan": {
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
                    "complexity": execution_plan.complexity_level,
                    "estimated_duration": execution_plan.estimated_duration_seconds
                }
            }
        )
        
        # Signal to parent ticket workflow
        parent_handle = workflow.get_external_workflow_handle(input_data.ticket_workflow_id)
        await parent_handle.signal("addMessage", plan_message.to_dict())
        
        workflow.logger.info(f"Signaled plan to parent workflow {input_data.ticket_workflow_id}")
    
    async def _signal_agent_result_to_parent(
        self,
        input_data: OrchestratorInput,
        agent_result: AgentExecutionResult
    ) -> None:
        """Signal individual agent result to parent ticket workflow immediately with full specialist output"""
        from data.ticket_models import ChatMessage
        from data.base_models import MessageType, AgentType as AT
        
        # Extract full specialist output from metadata
        full_output = agent_result.metadata.get("full_specialist_output", {})
        
        # Build additional_info based on agent type and available fields
        additional_info = {}
        
        # Order Specialist - actual fields: suggested_actions
        if agent_result.agent_type == AgentType.ORDER_SPECIALIST.value:
            if "suggested_actions" in full_output and full_output["suggested_actions"]:
                additional_info["suggested_actions"] = full_output["suggested_actions"]
        
        # Technical Specialist - actual fields: troubleshooting_steps, estimated_resolution_time
        elif agent_result.agent_type == AgentType.TECHNICAL_SPECIALIST.value:
            if "troubleshooting_steps" in full_output and full_output["troubleshooting_steps"]:
                additional_info["troubleshooting_steps"] = full_output["troubleshooting_steps"]
            if "estimated_resolution_time" in full_output and full_output["estimated_resolution_time"]:
                additional_info["estimated_resolution_time"] = full_output["estimated_resolution_time"]
        
        # Refund Specialist - actual fields: eligibility_assessment, required_documentation, processing_timeline
        elif agent_result.agent_type == AgentType.REFUND_SPECIALIST.value:
            if "eligibility_assessment" in full_output and full_output["eligibility_assessment"]:
                additional_info["eligibility_assessment"] = full_output["eligibility_assessment"]
            if "required_documentation" in full_output and full_output["required_documentation"]:
                additional_info["required_documentation"] = full_output["required_documentation"]
            if "processing_timeline" in full_output and full_output["processing_timeline"]:
                additional_info["processing_timeline"] = full_output["processing_timeline"]
        
        # General Support - actual fields: suggested_actions
        elif agent_result.agent_type == AgentType.GENERAL_SUPPORT.value:
            if "suggested_actions" in full_output and full_output["suggested_actions"]:
                additional_info["suggested_actions"] = full_output["suggested_actions"]
        
        # Male/Female Specialist - actual fields: measurements_collected, measurements_data, validation_status
        elif agent_result.agent_type in [AgentType.MALE_SPECIALIST.value, AgentType.FEMALE_SPECIALIST.value]:
            if "measurements_collected" in full_output:
                additional_info["measurements_collected"] = full_output["measurements_collected"]
            if "measurements_data" in full_output and full_output["measurements_data"]:
                additional_info["measurements_data"] = full_output["measurements_data"]
            if "validation_status" in full_output and full_output["validation_status"]:
                additional_info["validation_status"] = full_output["validation_status"]
        
        # Billing - actual fields: billing_complete, total_amount, payment_status, invoice_details
        elif agent_result.agent_type == AgentType.BILLING.value:
            if "billing_complete" in full_output:
                additional_info["billing_complete"] = full_output["billing_complete"]
            if "total_amount" in full_output:
                additional_info["total_amount"] = full_output["total_amount"]
            if "payment_status" in full_output and full_output["payment_status"]:
                additional_info["payment_status"] = full_output["payment_status"]
            if "invoice_details" in full_output and full_output["invoice_details"]:
                additional_info["invoice_details"] = full_output["invoice_details"]
        
        # Delivery - actual fields: delivery_scheduled, delivery_date, tracking_number, delivery_address
        elif agent_result.agent_type == AgentType.DELIVERY.value:
            if "delivery_scheduled" in full_output:
                additional_info["delivery_scheduled"] = full_output["delivery_scheduled"]
            if "delivery_date" in full_output and full_output["delivery_date"]:
                additional_info["delivery_date"] = full_output["delivery_date"]
            if "tracking_number" in full_output and full_output["tracking_number"]:
                additional_info["tracking_number"] = full_output["tracking_number"]
            if "delivery_address" in full_output and full_output["delivery_address"]:
                additional_info["delivery_address"] = full_output["delivery_address"]
        
        # Alteration - actual fields: alteration_needed, alteration_details, additional_cost
        elif agent_result.agent_type == AgentType.ALTERATION.value:
            if "alteration_needed" in full_output:
                additional_info["alteration_needed"] = full_output["alteration_needed"]
            if "alteration_details" in full_output and full_output["alteration_details"]:
                additional_info["alteration_details"] = full_output["alteration_details"]
            if "additional_cost" in full_output:
                additional_info["additional_cost"] = full_output["additional_cost"]
        
        agent_message = ChatMessage(
            id=str(workflow.uuid4()),
            ticket_id=input_data.ticket_id,
            content=f"{agent_result.response}",
            message_type=MessageType.AI_AGENT,
            agent_type=AT(agent_result.agent_type),
            timestamp=workflow.now(),
            additional_info=additional_info,  # Include specialist-specific fields
            metadata={
                "step_number": agent_result.step_number,
                "confidence": agent_result.confidence,
                "execution_time_ms": agent_result.execution_time_ms,
                "requires_escalation": agent_result.requires_escalation,
                "tool_results": agent_result.tool_results,
                "full_specialist_output": full_output  # Also keep in metadata for debugging
            }
        )
        
        # Signal to parent ticket workflow
        parent_handle = workflow.get_external_workflow_handle(input_data.ticket_workflow_id)
        await parent_handle.signal("addMessage", agent_message.to_dict())
        
        workflow.logger.info(
            f"Signaled {agent_result.agent_type} result with additional_info to parent workflow {input_data.ticket_workflow_id}"
        )
    
    async def _signal_final_response_to_parent(
        self,
        input_data: OrchestratorInput,
        orchestrator_output: OrchestratorOutput
    ) -> None:
        """Signal final synthesized response to parent ticket workflow"""
        from data.ticket_models import ChatMessage
        from data.base_models import MessageType, AgentType as AT
        
        final_response_message = ChatMessage(
            id=str(workflow.uuid4()),
            ticket_id=input_data.ticket_id,
            content=orchestrator_output.final_response,
            message_type=MessageType.AI_AGENT,
            agent_type=AT.ORCHESTRATOR,
            timestamp=workflow.now(),
            metadata={
                "orchestrator_synthesis": True,
                "confidence": orchestrator_output.confidence,
                "synthesis_reasoning": orchestrator_output.synthesis_reasoning,
                "agents_used": [r.agent_type for r in orchestrator_output.agent_results],
                "total_execution_time_ms": sum(
                    r.execution_time_ms for r in orchestrator_output.agent_results
                )
            }
        )
        
        # Signal to parent ticket workflow
        parent_handle = workflow.get_external_workflow_handle(input_data.ticket_workflow_id)
        await parent_handle.signal("addMessage", final_response_message.to_dict())
        
        workflow.logger.info(
            f"Signaled final response to parent workflow {input_data.ticket_workflow_id}"
        )
