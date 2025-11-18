"""MCP server configuration loader from YAML file."""

from typing import Dict, List, Tuple
import sys
import os
import yaml

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.base_models import AgentType

# Load configuration from YAML file
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "mcp_config.yaml")

def _load_config() -> dict:
    """Load MCP configuration from YAML file."""
    try:
        with open(_CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load MCP configuration from {_CONFIG_PATH}: {e}")

# Load configuration
_config = _load_config()

# Parse MCP Server Configuration
# Format: (server_name, port, description)
MCP_SERVERS: List[Tuple[str, int, str]] = [
    (server['name'], server['port'], server['description'])
    for server in _config['servers']
]

# MCP Server Base URL Template
MCP_BASE_URL = _config['base_url']

# Agent Type to MCP Server Mapping
# Maps each agent to the MCP servers it should use for tool discovery
AGENT_SERVER_MAPPING: Dict[AgentType, List[str]] = {
    AgentType[agent_type]: servers
    for agent_type, servers in _config['agent_server_mapping'].items()
}


def get_server_url(server_name: str) -> str:
    """Get the full URL for an MCP server by name."""
    for name, port, _ in MCP_SERVERS:
        if name == server_name:
            return MCP_BASE_URL.format(port=port)
    raise ValueError(f"Unknown MCP server: {server_name}")


def get_agent_servers(agent_type: AgentType) -> List[str]:
    """Get the list of MCP servers for a given agent type."""
    return AGENT_SERVER_MAPPING.get(agent_type, [])
