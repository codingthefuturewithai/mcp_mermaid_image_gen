"""MCP server package initialization"""

from mcp_mermaid_image_gen.config import load_config
from mcp_mermaid_image_gen.server.app import create_mcp_server

# Create server instance with default configuration
server = create_mcp_server(load_config())

__all__ = ["server", "create_mcp_server"]
