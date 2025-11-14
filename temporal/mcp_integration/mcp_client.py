"""MCP Client for HTTP-based Model Context Protocol communication."""

import dspy
from typing import List, Optional
import logging
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class MCPClient:
    """
    HTTP-based MCP client for communicating with MCP servers.
    
    Uses official MCP Python SDK with streamablehttp_client for persistent connections
    and tool discovery. Converts MCP tools to DSPy-compatible tools for agent use.
    """
    
    def __init__(self, server_url: str, server_name: str):
        """
        Initialize MCP client.
        
        Args:
            server_url: Base URL of the MCP server (e.g., "http://localhost:8001")
            server_name: Name identifier for the server (e.g., "order_server")
        """
        self.server_url = server_url.rstrip('/')
        self.server_name = server_name
        self.mcp_endpoint = f"{self.server_url}/mcp"
        self.session: Optional[ClientSession] = None
        self._tools_cache: Optional[List] = None
        self._dspy_tools_cache: Optional[List] = None
        self._connected = False
        self._read_stream = None
        self._write_stream = None
        self._client_context = None
        
    async def connect(self):
        """Establish connection to the MCP server using streamablehttp_client."""
        if self._connected:
            logger.warning(f"MCP client for {self.server_name} already connected")
            return
            
        try:
            # Establish streamable HTTP connection
            self._client_context = streamablehttp_client(self.mcp_endpoint)
            streams = await self._client_context.__aenter__()
            self._read_stream, self._write_stream, _ = streams
            
            # Create MCP session
            session_context = ClientSession(self._read_stream, self._write_stream)
            self.session = await session_context.__aenter__()
            
            # Initialize the MCP connection
            await self.session.initialize()
            
            self._connected = True
            logger.info(f"Connected to MCP server: {self.server_name} at {self.mcp_endpoint}")
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.server_name}: {e}")
            self._connected = False
            raise
    
    async def disconnect(self):
        """Close connection to the MCP server."""
        try:
            if self._client_context:
                await self._client_context.__aexit__(None, None, None)
            self._connected = False
            self._tools_cache = None
            self._dspy_tools_cache = None
            self.session = None
            logger.info(f"Disconnected from MCP server: {self.server_name}")
        except Exception as e:
            logger.error(f"Error disconnecting from {self.server_name}: {e}")
    

    
    async def list_tools(self) -> List:
        """
        Discover available tools from the MCP server.
        
        Returns:
            List of MCP tool objects
        """
        if self._tools_cache is not None:
            return self._tools_cache
        
        if not self._connected or not self.session:
            raise ConnectionError(f"Not connected to MCP server {self.server_name}")
        
        try:
            tools_response = await self.session.list_tools()
            tools = tools_response.tools
            
            # Cache the tools for future use
            self._tools_cache = tools
            
            logger.info(f"Discovered {len(tools)} tools from {self.server_name}")
            return tools
            
        except Exception as e:
            logger.error(f"Failed to list tools from {self.server_name}: {e}")
            return []
    
    async def create_dspy_tools(self) -> List:
        """
        Create DSPy-compatible tool functions from MCP tools.
        
        Uses dspy.Tool.from_mcp_tool() to convert MCP tools to DSPy tools.
        
        Returns:
            List of dspy.Tool objects that can be used with dspy.ReAct
        """
        if self._dspy_tools_cache is not None:
            return self._dspy_tools_cache
        
        if not self._connected or not self.session:
            raise ConnectionError(f"Not connected to MCP server {self.server_name}")
        
        try:
            # Get MCP tools
            mcp_tools = await self.list_tools()
            
            # Convert MCP tools to DSPy tools using official method
            dspy_tools = []
            for mcp_tool in mcp_tools:
                dspy_tool = dspy.Tool.from_mcp_tool(self.session, mcp_tool)
                dspy_tools.append(dspy_tool)
            
            # Cache for reuse
            self._dspy_tools_cache = dspy_tools
            
            logger.info(f"Converted {len(dspy_tools)} MCP tools to DSPy tools for {self.server_name}")
            return dspy_tools
            
        except Exception as e:
            logger.error(f"Failed to create DSPy tools from {self.server_name}: {e}")
            return []
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected to the server."""
        return self._connected
    
    async def health_check(self) -> bool:
        """
        Perform health check on the MCP server.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(self.server_url)
                if response.status_code == 200:
                    server_info = response.json()
                    return server_info.get("status") == "running"
            return False
        except Exception as e:
            logger.warning(f"Health check failed for {self.server_name}: {e}")
            return False
