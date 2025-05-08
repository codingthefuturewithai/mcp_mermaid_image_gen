"""MCP server implementation with Echo tool"""

import sys
import os
import asyncio
import click
from typing import Optional

# Add project root to sys.path
# __file__ is mcp_mermaid_image_gen/server/app.py
# os.path.dirname(__file__) is mcp_mermaid_image_gen/server
# os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) is /Users/timkitchens/projects/ai-projects/mcp_mermaid_image_gen
PROJECT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_DIR)

from mcp import types
from mcp.server.fastmcp import FastMCP, Image

# Use absolute imports now that project root is in sys.path
from mcp_mermaid_image_gen.config import ServerConfig, load_config
from mcp_mermaid_image_gen.logging_config import setup_logging, logger
from mcp_mermaid_image_gen.tools.echo import echo


def create_mcp_server(config: Optional[ServerConfig] = None) -> FastMCP:
    """Create and configure the MCP server instance"""
    if config is None:
        config = load_config()
    
    # Set up logging first
    # Use the imported logger directly if setup_logging configures the root logger
    # or ensure logger object from logging_config is used correctly.
    # For now, assuming setup_logging handles global logger config or returns one.
    setup_logging(config) 
    
    # Get a logger instance for this module, assuming setup_logging configured it
    module_logger = logger # Use the imported logger from logging_config

    module_logger.info(f"Initializing MCP Server with name: {config.name}")
    server = FastMCP(config.name)

    # Register all tools with the server
    module_logger.info("Registering tools...")
    register_tools(server)
    module_logger.info("Tool registration complete.")

    return server


def register_tools(mcp_server: FastMCP) -> None:
    """Register all MCP tools with the server"""
    module_logger = logger # Use the imported logger

    @mcp_server.tool(
        name="echo",
        description="Echo back the input text with optional case transformation",
    )
    def echo_tool(text: str, transform: Optional[str] = None) -> types.TextContent:
        """Wrapper around the echo tool implementation"""
        module_logger.debug(f"Echo tool called with text: '{text}', transform: '{transform}'")
        result = echo(text, transform)
        module_logger.debug(f"Echo tool returning: '{result.text}'")
        return result


# Create a server instance that can be imported by the MCP CLI
# This line should use the module_logger if it's defined by this point,
# or we ensure logger is configured before this print.
# For safety, let's assume logger from logging_config is fine.
logger.info("Creating MCP server instance for module export...")
server = create_mcp_server()
logger.info("MCP server instance created.")


@click.command()
@click.option("--port", default=3001, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type (stdio or sse)",
)
def main(port: int, transport: str) -> int:
    """Run the server with specified transport."""
    # Ensure logger is available here too
    cli_logger = logger # Use the imported logger

    cli_logger.info(f"Attempting to start server with transport: {transport}, port: {port if transport == 'sse' else 'N/A'}")
    try:
        # If server is already created globally, we use that instance.
        # The 'server' variable created above is the one to use.
        if transport == "stdio":
            cli_logger.info("Running server in stdio mode.")
            asyncio.run(server.run_stdio_async())
        else:
            server.settings.port = port # Configure port for SSE on the global server instance
            cli_logger.info(f"Running server in sse mode on port {port}.")
            asyncio.run(server.run_sse_async())
        cli_logger.info("Server finished running.")
        return 0
    except KeyboardInterrupt:
        cli_logger.info("Server stopped by user.")
        return 0
    except Exception as e:
        cli_logger.error(f"Failed to start server: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    # This is when app.py is run as the main script.
    # Ensure logger is available.
    main_logger = logger # Use the imported logger
    main_logger.info("app.py executed as main script.")
    # sys.exit(main()) # click commands usually handle sys.exit
    main()