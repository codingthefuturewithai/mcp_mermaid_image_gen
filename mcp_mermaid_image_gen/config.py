"""Server configuration for MCP Mermaid Image Gen MCP server"""

import os
from dataclasses import dataclass

@dataclass
class ServerConfig:
    """Configuration for the MCP server"""
    name: str = "MCP Mermaid Image Gen"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


def load_config() -> ServerConfig:
    """Load server configuration from environment or defaults"""
    return ServerConfig(
        name=os.getenv("MCP_SERVER_NAME", "MCP Mermaid Image Gen"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
