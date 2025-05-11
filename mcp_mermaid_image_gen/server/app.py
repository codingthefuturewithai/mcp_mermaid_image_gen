"""MCP server implementation for Mermaid diagram generation"""

import sys
import os
import asyncio
import click
import base64
from typing import Optional
import tempfile
import pathlib
import logging

# Add project root to sys.path
PROJECT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_DIR)

from mcp import types
from mcp.server.fastmcp import FastMCP

# Use absolute imports now that project root is in sys.path
from mcp_mermaid_image_gen.config import ServerConfig, load_config
from mcp_mermaid_image_gen.logging_config import setup_logging, logger
from mcp_mermaid_image_gen.tools.mermaid_renderer import render_mermaid_to_file


def create_mcp_server(config: Optional[ServerConfig] = None) -> FastMCP:
    """Create and configure the MCP server instance"""
    if config is None:
        config = load_config()

    server = FastMCP(name=config.name)
    
    # Register tools
    register_tools(server)
    
    return server


def register_tools(mcp_server: FastMCP) -> None:
    """Register all MCP tools with the server."""
    
    @mcp_server.tool(
        name="generate_mermaid_diagram_file",
        description="""Generate a Mermaid diagram and save it to a local file system directory.

SYSTEM PREREQUISITES:
- Node.js must be installed (v14 or higher)
- Mermaid CLI must be installed globally: npm install -g @mermaid-js/mermaid-cli
- The 'mmdc' command must be available in the system PATH
- Python 3.8 or higher with MCP tools installed

IMPORTANT TRANSPORT & ACCESS REQUIREMENTS:
- Works with both STDIO and SSE transport modes
- REQUIRES: The MCP client (e.g., AI assistant) must have access to the local file system where the image is saved
- The client must have write permissions for the specified folder

PARAMETER GUIDANCE:
- code: Valid Mermaid diagram syntax (see https://mermaid.js.org/)
- folder: Absolute or relative path to an existing directory with write permissions
- name: Filename for the diagram (extension can determine format if format not specified)
- theme: Theme name for the diagram. MUST be one of: ["default", "neutral", "dark", "forest", "base"]
  - default: Default theme for all diagrams
  - neutral: Great for black and white documents that will be printed
  - dark: Works well with dark-colored elements or dark-mode
  - forest: Contains shades of green
  - base: The only theme that can be modified for customization
- backgroundColor: Optional hex color code (e.g., '#FFFFFF') or color name (e.g., 'white', 'transparent')
- format: Output format. MUST be one of: ["svg", "png", "pdf"]. If not specified:
  1. Inferred from filename extension if provided (e.g., "diagram.svg" -> svg)
  2. Defaults to "png" if no valid extension found

RESPONSE:
- Returns the absolute path to the generated file
- The client must be able to access this path to use the generated image

USE CASE:
Best suited for scenarios where:
1. The client needs to persist the diagram to disk
2. The client has local file system access
3. The client needs to reference the image file path in subsequent operations"""
    )
    async def generate_mermaid_diagram_file(
        code: str,
        folder: str,
        name: str,
        theme: str = None,
        backgroundColor: str = None,
        format: str = None
    ) -> types.TextContent:
        """
        Generate a Mermaid diagram and save it to a file.
        
        Args:
            code (str): The Mermaid diagram code (must be valid Mermaid syntax)
            folder (str): The folder where to save the diagram (must exist and be writable)
            name (str): The name for the diagram file (extension can determine format)
            theme (str): Theme name (default, neutral, dark, forest, or base)
            backgroundColor (str): Background color for the diagram (hex code or color name)
            format (str): Output format (svg, png, or pdf)
            
        Returns:
            TextContent: The absolute path where the file was saved
            
        Raises:
            ValueError: If the folder doesn't exist or isn't writable
            ValueError: If the Mermaid CLI (mmdc) is not installed
            ValueError: If the Mermaid syntax is invalid
            ValueError: If an invalid theme or format is specified
        """
        try:
            output_path = await render_mermaid_to_file(
                code=code,
                output_dir=folder,
                name=name,
                theme=theme,
                background_color=backgroundColor,
                format=format
            )
            return types.TextContent(type="text", text=str(output_path))
        except Exception as e:
            logger.error(f"Error generating Mermaid diagram: {e}")
            return types.TextContent(type="text", text=f"Error: {str(e)}")

    @mcp_server.tool(
        name="generate_mermaid_diagram_stream",
        description="""Generate a Mermaid diagram and return it directly as a base64-encoded image.

SYSTEM PREREQUISITES:
- Node.js must be installed (v14 or higher)
- Mermaid CLI must be installed globally: npm install -g @mermaid-js/mermaid-cli
- The 'mmdc' command must be available in the system PATH
- Python 3.8 or higher with MCP tools installed
- MCP client must support SSE transport and binary/base64 image handling

IMPORTANT TRANSPORT REQUIREMENTS:
- REQUIRES SSE TRANSPORT MODE ONLY
- Will NOT work with STDIO transport
- DO NOT use this endpoint if your MCP client doesn't support SSE transport
- DO NOT use this endpoint if your client can't handle binary/base64 image data

PARAMETER GUIDANCE:
- code: Valid Mermaid diagram syntax (see https://mermaid.js.org/)
- theme: Theme name for the diagram. MUST be one of: ["default", "neutral", "dark", "forest", "base"]
  - default: Default theme for all diagrams
  - neutral: Great for black and white documents that will be printed
  - dark: Works well with dark-colored elements or dark-mode
  - forest: Contains shades of green
  - base: The only theme that can be modified for customization
- backgroundColor: Optional hex color code (e.g., '#FFFFFF') or color name (e.g., 'white', 'transparent')
- format: Output format. MUST be one of: ["svg", "png", "pdf"]. Defaults to "png" if not specified.

RESPONSE:
- Returns the diagram as a base64-encoded image in the specified format
- No file system access or permissions required
- Image data is streamed directly back to the client

USE CASE:
Best suited for scenarios where:
1. The client is using SSE transport mode
2. The client can handle base64-encoded image data
3. No need to persist the image to disk
4. No file system access is available or desired"""
    )
    async def generate_mermaid_diagram_stream(
        code: str,
        theme: str = None,
        backgroundColor: str = None,
        format: str = None
    ) -> types.ImageContent:
        """
        Generate a Mermaid diagram and return it as an image stream.
        
        Args:
            code (str): The Mermaid diagram code (must be valid Mermaid syntax)
            theme (str): Theme name (default, neutral, dark, forest, or base)
            backgroundColor (str): Background color for the diagram (hex code or color name)
            format (str): Output format (svg, png, or pdf)
            
        Returns:
            ImageContent: The generated diagram as a base64-encoded image
            
        Raises:
            ValueError: If the Mermaid CLI (mmdc) is not installed
            ValueError: If the Mermaid syntax is invalid
            ValueError: If an invalid theme or format is specified
            RuntimeError: If used with non-SSE transport
        """
        try:
            # Create a temporary directory for the output
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = await render_mermaid_to_file(
                    code=code,
                    output_dir=temp_dir,
                    name=f"temp.{format if format else 'png'}", # Use format in temp filename
                    theme=theme,
                    background_color=backgroundColor,
                    format=format
                )
                
                # Read the generated image
                with open(output_path, "rb") as f:
                    image_bytes = f.read()
                
                # Convert to base64
                image_b64 = base64.b64encode(image_bytes).decode()
                
                # Determine MIME type based on format
                format_mime = {
                    "svg": "image/svg+xml",
                    "png": "image/png",
                    "pdf": "application/pdf"
                }
                mime_type = format_mime.get(format.lower() if format else "png", "image/png")
                
                return types.ImageContent(
                    type="image",
                    data=image_b64,
                    mimeType=mime_type
                )
        except Exception as e:
            logger.error(f"Error generating Mermaid diagram: {e}")
            raise


# Create server instance that can be imported by MCP CLI
server = create_mcp_server()


@click.command()
@click.option("--port", default=3001, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type (stdio or sse)"
)
def main(port: int, transport: str) -> int:
    """Run the server with specified transport."""
    try:
        # Create server with any command line overrides
        config = load_config()
        
        global server
        server = create_mcp_server(config)

        if transport == "stdio":
            asyncio.run(server.run_stdio_async())
        else:
            server.settings.port = port
            asyncio.run(server.run_sse_async())
        return 0
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())