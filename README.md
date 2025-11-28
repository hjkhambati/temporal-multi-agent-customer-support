# 🤖 Temporal Multi-Agent Customer Support System

> **Production-ready customer support system with intelligent AI orchestrator, dependency-aware agent execution, and full transparency**

[![Temporal](https://img.shields.io/badge/Temporal-Workflows-blue)](https://temporal.io)
[![DSPy](https://img.shields.io/badge/DSPy-ChainOfThought%20%26%20ReAct-green)](https://dspy.ai)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)](https://streamlit.io)

## 🎯 What Makes This Special

✅ **Orchestrator Agent**: Intelligent planning with dependency-aware execution  
✅ **Context Sharing**: Agents receive outputs from previous agents (no redundant questions)  
✅ **Agent-Driven**: Zero hardcoded business logic - agents make all decisions using tools  
✅ **Dual Flow Support**: Purchase flow (measurements → billing → delivery) + Post-purchase (orders → refunds → tech support)  
✅ **Real-Time Transparency**: All orchestrator reasoning visible to users  
✅ **Production-Ready**: Built on Temporal's reliable platform with persistent data  

## 🏗️ System Architecture

![System Architecture](architecture/temporal_multi_agent.svg)

### Agent Flow Example
```
Customer: "My laptop from order ORD-123 is broken, need refund!"

🤖 Orchestrator Plans:
  Step 1: OrderSpecialist (verify order) → no dependencies
  Step 2: TechnicalSpecialist (diagnose) → depends on Step 1
  Step 3: RefundSpecialist (process) → depends on Steps 1+2

🚀 Execution:
  Stage 1: OrderSpecialist finds order details
  Stage 2: TechnicalSpecialist receives order context → diagnoses hardware defect
  Stage 3: RefundSpecialist receives order + diagnosis → processes $1,299.99 refund

🎯 Result: Single unified response combining all findings
```

## 🚀 Quick Start

### Prerequisites
```bash
- Python 3.11+
- Temporal CLI (download from: https://github.com/temporalio/cli/releases)
- Google Gemini API key
```

### 1. Setup Environment
```powershell
# Clone and install
pip install -r requirements.txt

# Create .env file
GEMINI_API_KEY=your_gemini_api_key_here
TEMPORAL_ADDRESS=localhost:7233
TASK_QUEUE=multi-agent-support
```

### 2. Run System (4 Terminals Required)

#### Terminal 1: Temporal Server
```powershell
temporal server start-dev
```
**Purpose**: Core orchestration server (`localhost:7233`)  
**Web UI**: http://localhost:8233  
**Status**: Must be running first

#### Terminal 2: Worker
```powershell
python temporal/worker.py
```
**Purpose**: Registers all workflows and activities  
**Wait for**: "Starting multi-agent customer support worker..."

#### Terminal 3: Customer Interface
```powershell
streamlit run streamlit/customer_app.py --server.port 8502
```
**Access**: http://localhost:8502  
**Purpose**: Customer ticket creation and chat

#### Terminal 4: Admin Interface
```powershell
streamlit run streamlit/admin_app.py --server.port 8501
```
**Access**: http://localhost:8501  
**Purpose**: Admin dashboard and human-in-the-loop intervention
- Keep this terminal running

---

#### Terminal 3: Customer Interface
```powershell
streamlit run streamlit/customer_app.py --server.port 8502
```
**Purpose**: Customer-facing ticket creation and chat interface
- Access at: http://localhost:8502
- Customers can create tickets and chat with AI agents

### 3. Test the System
```
Customer App (localhost:8502): "I want to buy a shirt and check my order ORD-123"

🔄 Watch the magic:
1. 🤖 Orchestrator creates execution plan
2. 👤 Multiple specialists execute (with dependencies)
3. 🎯 Unified response delivered

Access Points: Customer (8502) | Admin (8501) | Temporal UI (8233)
```

## 🧩 Core Components

### 🎯 10 Specialist Agents

**Purchase Flow** (for buying items):
- **Male/Female Specialist**: Measurements, size recommendations, product selection
- **Billing Agent**: Payment processing, invoices, discounts  
- **Delivery Agent**: Address validation, delivery scheduling, tracking
- **Alteration Agent**: Custom alterations, cost calculation

**Post-Purchase Flow** (existing orders):
- **Order Specialist**: Tracking, modifications, cancellations
- **Technical Specialist**: Troubleshooting, diagnostics, warranty
- **Refund Specialist**: Returns, refunds, eligibility checks
- **General Support**: FAQ, account management, callbacks

### 🧠 Orchestrator Intelligence

**Planning Phase** (DSPy ChainOfThought):
```python
ExecutionPlan:
  - steps: List[ExecutionStep]           # Each step = one agent
  - strategy: "parallel" | "sequential"  # Execution approach
  - dependencies: agent relationships    # Who needs what from whom
```

**Execution Phase** (Dependency-Aware):
- **Stage 1**: Independent agents (parallel)
- **Stage 2**: Dependent agents receive context from Stage 1
- **Stage N**: Final agents with accumulated context

**Synthesis Phase**: Combines all outputs into unified response

### 🔧 Tool-Based Reasoning (DSPy.React)

Each agent has domain-specific tools:
```python
order_react = dspy.ReAct(
    OrderSpecialistResponse,
    tools=[
        search_orders,           # Find orders in database  
        check_order_status,      # Get tracking info
        ask_user_question,       # Ask for clarification
        modify_order,            # Cancel/change order
    ]
)
```

**Agent autonomously**:
1. Analyzes customer message
2. Calls appropriate tools to gather data
3. Asks clarifying questions when needed
4. Makes decisions based on tool results
5. Returns structured response

## 💾 Data Persistence

All data persists in JSON files (`temporal/data/persistence_data/`):
```
📁 persistence_data/
├── 📄 catalog.json          # Product inventory
├── 📄 customers.json        # Customer accounts  
├── 📄 orders.json           # Historical orders
├── 📄 purchases.json        # Active purchase orders
├── 📄 measurements.json     # Customer measurements
├── 📄 alterations.json      # Alteration requests
├── 📄 billing.json          # Payment records
└── 📄 delivery.json         # Delivery schedules
```

**Benefits**: Data survives restarts, easy backup/restore, clear separation

## 🎭 Example Scenarios

### Scenario 1: Multi-Intent Query
```
Customer: "I want to buy a shirt and also return my defective laptop"

🤖 Orchestrator Plans:
  Step 1: MaleSpecialist (measurements) - no dependencies
  Step 2: OrderSpecialist (find laptop order) - no dependencies  
  Step 3: TechnicalSpecialist (diagnose laptop) - depends on Step 2
  Step 4: BillingAgent (process shirt payment) - depends on Step 1
  Step 5: RefundSpecialist (process laptop refund) - depends on Steps 2,3

🚀 Execution: Parallel where possible, sequential for dependencies
🎯 Result: "I've collected your measurements for the shirt, found your laptop order, 
          diagnosed the hardware issue, processed your shirt payment, and 
          initiated a $1,299 refund for the defective laptop."
```

### Scenario 2: Agent Questions
```
Customer: "I need help with my order"
Agent: "What is your order number?"
Customer: "ORD-12345"  
Agent: "Your order shipped yesterday. Tracking: TRK-789"
```
**Behind the scenes**: Agent calls `ask_user_question()` → creates UserQuestionWorkflow → state-based routing → seamless Q&A

## 🔍 Monitoring & Debugging

### Temporal Web UI (localhost:8233)
- **Timeline**: See parallel/sequential execution  
- **Event History**: All signals, activities, child workflows
- **Current State**: Chat history, ticket status, pending questions
- **Agent Outputs**: Each specialist's structured response

### Chat History Structure
```json
{
  "content": "I've processed your refund of $1,299.99",
  "agent_type": "REFUND_SPECIALIST", 
  "additional_info": {
    "eligibility_assessment": "Eligible - Hardware defect",
    "refund_amount": 1299.99,
    "processing_timeline": "3-5 business days"
  }
}
```

```
📁 temporal/
├── 🔄 workflows/                    # Temporal orchestration
│   ├── ticket_workflow.py          # Main workflow
│   ├── user_question_workflow.py   # Agent Q&A handling
│   └── agents/                     # 10 specialist agents
├── ⚡ activities/                   # DSPy.React implementations  
│   └── tools/                      # Domain-specific tools
├── 📊 data/                        # Models & persistent data
│   ├── persistence_data/           # JSON storage (8 files)
│   └── persistent_data.py          # Data layer
└── 🖥️ streamlit/                   # User interfaces
    ├── customer_app.py    # Customer chat
    └── admin_app.py       # Admin dashboard
```

## 🚀 Key Features

### ✨ What Sets This Apart
- **🧠 Intelligent Orchestration**: Plans execution based on query complexity
- **🔗 Dependency Management**: Agents execute in order when they need each other's data
- **🎯 Context Accumulation**: Later agents receive earlier agents' findings (no redundant questions)
- **📱 Dual Flow Support**: Purchase flow + Post-purchase flow
- **👁️ Full Transparency**: All orchestrator reasoning visible in chat
- **⚡ Real-Time Updates**: See each agent's work as it happens
- **💾 Persistent Data**: All purchases, orders, measurements survive restarts
- **🤝 Human-in-the-Loop**: Admin can intervene at any point

### 🛠️ Development Features
- **🔧 Tool-Based Agents**: DSPy.React with domain-specific tools
- **📈 Production-Ready**: Built on Temporal's reliable platform
- **🔍 Observable**: Full audit trails via Temporal Web UI
- **🚀 Scalable**: Handle concurrent conversations
- **📋 Extensible**: Easy to add new agents and tools

## 🎓 Architecture Principles

1. **Agent-Driven**: Zero hardcoded business logic - agents decide everything
2. **Tool-Based Reasoning**: Agents use tools like humans use apps
3. **Planning-Based Coordination**: Orchestrator intelligently plans execution
4. **Context Passing**: Accumulated knowledge flows between dependent agents
5. **State-Based Routing**: Single entry point with smart message routing

## 🏆 Built With

- **[Temporal](https://temporal.io)** - Reliable workflow orchestration
- **[DSPy](https://dspy.ai)** - Agent reasoning framework  
- **[Google Gemini](https://ai.google.dev/)** - LLM capabilities
- **[Streamlit](https://streamlit.io)** - Rapid UI development

- **[Deepeval-testing](https://gemini.google.com/share/6dd17a6d0a22)

---

**🚀 Ready to revolutionize customer support? Clone and run in 4 terminals!**
