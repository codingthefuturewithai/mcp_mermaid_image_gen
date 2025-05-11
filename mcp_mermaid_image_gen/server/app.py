"""MCP server implementation for Mermaid diagram generation"""

import sys
import os
import asyncio
import click
from typing import Optional
import tempfile
import pathlib
import logging
import base64

# Add project root to sys.path
# __file__ is mcp_mermaid_image_gen/server/app.py
# os.path.dirname(__file__) is mcp_mermaid_image_gen/server
# os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) is /Users/timkitchens/projects/ai-projects/mcp_mermaid_image_gen
PROJECT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_DIR)

from mcp import types
from mcp.server.fastmcp import FastMCP

# Use absolute imports now that project root is in sys.path
from mcp_mermaid_image_gen.config import ServerConfig, load_config
from mcp_mermaid_image_gen.logging_config import setup_logging, logger
from mcp_mermaid_image_gen.tools.mermaid_renderer import render_mermaid_to_file


def register_tools(mcp_server: FastMCP) -> None:
    """Register MCP tools with the server"""
    module_logger = logger

    @mcp_server.tool(
        name="generate_mermaid_diagram_file",
        description="Generates a Mermaid diagram from code and saves it to a specified file path (folder + name)."
    )
    async def mermaid_stdio_tool_logic(
        code: str, 
        folder: str,  # Absolute path to the folder
        name: str,    # Filename (e.g., "diagram.png")
        theme: Optional[str] = None,
        backgroundColor: Optional[str] = None
    ) -> str: 
        tool_logger = logging.getLogger(f"{__name__}.mermaid_stdio_tool")
        tool_logger.info(f"generate_mermaid_diagram_file called. Folder: {folder}, Name: {name}")
        output_path = pathlib.Path(folder) / name
        
        try:
            await render_mermaid_to_file(
                code,
                str(output_path.resolve()),
                theme=theme,
                backgroundColor=backgroundColor
            )
            tool_logger.info(f"Mermaid diagram saved to: {output_path.resolve()}")
            return str(output_path.resolve())
        except FileNotFoundError: 
            tool_logger.error("mmdc command not found. Cannot generate diagram.")
            raise ValueError("mmdc command not found. Ensure @mermaid-js/mermaid-cli is installed globally.")
        except ValueError as e: 
            tool_logger.error(f"Error generating diagram for file: {e}")
            raise
        except Exception as e:
            tool_logger.error(f"Unexpected error in generate_mermaid_diagram_file: {e}", exc_info=True)
            raise ValueError(f"An unexpected error occurred in file diagram generation: {e}")

    @mcp_server.tool(
        name="generate_mermaid_diagram_stream",
        description="Generates a Mermaid diagram from code and streams it back as an image."
    )
    async def mermaid_sse_tool_logic(
        code: str, 
        theme: Optional[str] = None,
        backgroundColor: Optional[str] = None
    ) -> types.ImageContent:
        tool_logger = logging.getLogger(f"{__name__}.mermaid_sse_tool")
        tool_logger.info("generate_mermaid_diagram_stream called.")
        tmp_output_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_output_file:
                tmp_output_path = tmp_output_file.name
            
            tool_logger.debug(f"Temporary file for SSE stream: {tmp_output_path}")
            await render_mermaid_to_file(
                code,
                tmp_output_path,
                theme=theme,
                backgroundColor=backgroundColor
            )
            tool_logger.info(f"Mermaid diagram generated for streaming from: {tmp_output_path}")
            
            # Read the image bytes and base64 encode them
            with open(tmp_output_path, 'rb') as f:
                image_bytes = f.read()
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            return types.ImageContent(
                type="image",
                data=image_b64,
                mimeType="image/png"
            )
        except FileNotFoundError: 
            tool_logger.error("mmdc command not found. Cannot generate diagram.")
            raise ValueError("mmdc command not found. Ensure @mermaid-js/mermaid-cli is installed globally.")
        except ValueError as e: 
            tool_logger.error(f"Error generating diagram for stream: {e}")
            raise
        except Exception as e:
            tool_logger.error(f"Unexpected error in generate_mermaid_diagram_stream: {e}", exc_info=True)
            raise ValueError(f"An unexpected error occurred in stream diagram generation: {e}")
        finally:
            if tmp_output_path and os.path.exists(tmp_output_path):
                os.remove(tmp_output_path)
                tool_logger.debug(f"Removed temporary SSE image file: {tmp_output_path}")

    module_logger.info("All Mermaid tools registered.")


def create_mcp_server(config: Optional[ServerConfig] = None) -> FastMCP:
    """Create and configure the MCP server instance"""
    if config is None:
        config = load_config()
    
    setup_logging(config)
    module_logger = logger

    module_logger.info(f"Initializing MCP Server with name: {config.name}")
    server = FastMCP(config.name)
    
    # Register tools
    register_tools(server)
    module_logger.info("Tool registration complete.")
    module_logger.info("MCP server instance created.")

    return server


# Create server instance that can be imported by MCP CLI
server = create_mcp_server()


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
    cli_logger = logger
    cli_logger.info(f"main() called with transport: {transport}, port: {port if transport == 'sse' else 'N/A'}")

    try:
        # Use the global server instance
        if transport == "stdio":
            cli_logger.info("Running server in stdio mode.")
            asyncio.run(server.run_stdio_async())
        else:
            server.settings.port = port
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
    sys.exit(main())