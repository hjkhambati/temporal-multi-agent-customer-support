"""MCP server configuration and agent-to-server mapping."""

from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.base_models import AgentType

# MCP Server Configuration
# Format: (server_name, port, description)
MCP_SERVERS: List[Tuple[str, int, str]] = [
    ("alteration_server", 8001, "Alteration Server"),
    ("billing_server", 8002, "Billing Server"),
    ("delivery_server", 8003, "Delivery Server"),
    ("general_server", 8004, "General Support Server"),
    ("male_specialist_server", 8005, "Male Specialist Server"),
    ("female_specialist_server", 8006, "Female Specialist Server"),
    ("order_server", 8007, "Order Server"),
    ("refund_server", 8008, "Refund Server"),
    ("technical_server", 8009, "Technical Support Server"),
]

# Agent Type to MCP Server Mapping
# Maps each agent to the MCP servers it should use for tool discovery
AGENT_SERVER_MAPPING: Dict[AgentType, List[str]] = {
    AgentType.ORDER_SPECIALIST: ["order_server", "billing_server"],
    AgentType.TECHNICAL_SPECIALIST: ["technical_server", "general_server"],
    AgentType.REFUND_SPECIALIST: ["refund_server", "order_server"],
    AgentType.GENERAL_SUPPORT: ["general_server"],
    AgentType.MALE_SPECIALIST: ["male_specialist_server", "order_server"],
    AgentType.FEMALE_SPECIALIST: ["female_specialist_server", "order_server"],
    AgentType.BILLING: ["billing_server", "order_server"],
    AgentType.DELIVERY: ["delivery_server", "order_server"],
    AgentType.ALTERATION: ["alteration_server", "order_server"],
}

# MCP Server Base URL Template
MCP_BASE_URL = "http://localhost:{port}"


def get_server_url(server_name: str) -> str:
    """Get the full URL for an MCP server by name."""
    for name, port, _ in MCP_SERVERS:
        if name == server_name:
            return MCP_BASE_URL.format(port=port)
    raise ValueError(f"Unknown MCP server: {server_name}")


def get_agent_servers(agent_type: AgentType) -> List[str]:
    """Get the list of MCP servers for a given agent type."""
    return AGENT_SERVER_MAPPING.get(agent_type, [])
