"""MCP Connection Manager for persistent server connections."""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_integration.mcp_client import MCPClient
from mcp_integration.config import MCP_SERVERS, AGENT_SERVER_MAPPING, get_server_url, get_agent_servers
from data.base_models import AgentType

logger = logging.getLogger(__name__)


class MCPConnectionManager:
    """
    Global MCP connection manager for maintaining persistent connections to all MCP servers.
    
    This manager maintains a single persistent connection per MCP server and provides
    tool discovery and execution capabilities for activities.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self._connections: Dict[str, MCPClient] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize_connections(self):
        """
        Initialize persistent connections to all MCP servers.
        
        This should be called once at worker startup.
        """
        async with self._lock:
            if self._initialized:
                logger.warning("MCP connections already initialized")
                return
            
            logger.info(f"Initializing connections to {len(MCP_SERVERS)} MCP servers...")
            
            # Initialize connections to all servers
            for server_name, port, description in MCP_SERVERS:
                try:
                    server_url = get_server_url(server_name)
                    client = MCPClient(server_url, server_name)
                    await client.connect()
                    self._connections[server_name] = client
                    logger.info(f"✓ Connected to {description} on port {port}")
                except Exception as e:
                    logger.error(f"✗ Failed to connect to {description} on port {port}: {e}")
                    # Continue initialization even if one server fails
            
            self._initialized = True
            logger.info(f"Successfully connected to {len(self._connections)}/{len(MCP_SERVERS)} MCP servers")
    
    async def close_all_connections(self):
        """
        Close all MCP server connections.
        
        This should be called during worker shutdown.
        """
        async with self._lock:
            if not self._initialized:
                return
            
            logger.info("Closing all MCP connections...")
            
            for server_name, client in self._connections.items():
                try:
                    await client.disconnect()
                    logger.info(f"Closed connection to {server_name}")
                except Exception as e:
                    logger.error(f"Error closing connection to {server_name}: {e}")
            
            self._connections.clear()
            self._initialized = False
            logger.info("All MCP connections closed")
    
    def get_client(self, server_name: str) -> Optional[MCPClient]:
        """
        Get an MCP client by server name.
        
        Args:
            server_name: Name of the MCP server (e.g., "order_server")
            
        Returns:
            MCPClient instance or None if not found
        """
        if not self._initialized:
            logger.warning("MCP connections not initialized")
            return None
        
        return self._connections.get(server_name)
    
    async def get_tools_for_agent(self, agent_type: AgentType, include_static_tools: Optional[List[Callable]] = None) -> List[Callable]:
        """
        Get all tools (MCP + static) for a specific agent type.
        
        Args:
            agent_type: Type of agent requesting tools
            include_static_tools: Optional list of static tools to include (e.g., ask_user_question)
            
        Returns:
            Combined list of MCP and static tool functions
        """
        if not self._initialized:
            logger.warning("MCP connections not initialized, returning only static tools")
            return include_static_tools or []
        
        server_names = get_agent_servers(agent_type)
        
        if not server_names:
            logger.warning(f"No MCP servers configured for agent type {agent_type}")
            return include_static_tools or []
        
        all_tools = []
        
        # Collect tools from all assigned MCP servers
        for server_name in server_names:
            client = self.get_client(server_name)
            
            if not client or not client.is_connected:
                logger.warning(f"MCP server {server_name} not available for {agent_type}")
                continue
            
            try:
                # Get DSPy-compatible tools from this server
                server_tools = await client.create_dspy_tools()
                all_tools.extend(server_tools)
                logger.debug(f"Added {len(server_tools)} tools from {server_name} for {agent_type}")
            except Exception as e:
                logger.error(f"Failed to get tools from {server_name}: {e}")
        
        # Add static tools (like ask_user_question, validate_user_response)
        if include_static_tools:
            all_tools.extend(include_static_tools)
            logger.debug(f"Added {len(include_static_tools)} static tools for {agent_type}")
        
        logger.info(f"Loaded {len(all_tools)} total tools for {agent_type}")
        return all_tools
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all MCP servers.
        
        Returns:
            Dictionary mapping server names to health status
        """
        results = {}
        
        for server_name, client in self._connections.items():
            try:
                is_healthy = await client.health_check()
                results[server_name] = is_healthy
            except Exception as e:
                logger.error(f"Health check failed for {server_name}: {e}")
                results[server_name] = False
        
        return results
    
    @property
    def is_initialized(self) -> bool:
        """Check if the connection manager is initialized."""
        return self._initialized
    
    @property
    def connected_servers(self) -> List[str]:
        """Get list of currently connected server names."""
        return [
            name for name, client in self._connections.items()
            if client.is_connected
        ]
    
    def get_connection_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed connection status for all servers.
        
        Returns:
            Dictionary with connection details for each server
        """
        status = {}
        
        for server_name, client in self._connections.items():
            status[server_name] = {
                "connected": client.is_connected,
                "server_url": client.server_url,
                "tools_cached": client._tools_cache is not None,
                "tool_count": len(client._tools_cache) if client._tools_cache else 0
            }
        
        return status


# Global singleton instance
mcp_manager = MCPConnectionManager()
