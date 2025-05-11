# MCP Mermaid Image Gen

An MCP server that generates diagrams from Mermaid code in multiple formats (SVG, PNG, PDF). This server enables AI assistants and other MCP clients to create diagrams using the Mermaid diagram syntax, with support for multiple themes, formats, and customizable backgrounds.

## Overview

This MCP server wraps the Mermaid CLI (`@mermaid-js/mermaid-cli`) to provide diagram generation capabilities through the Model Context Protocol (MCP). It offers two operation modes:

1. File-based: Save diagrams to disk and return the file path
2. Stream-based: Return the diagram directly as base64-encoded data

Both modes work with either STDIO or SSE transport, but the stream-based mode requires an MCP client capable of handling image data.

The server is designed to be used by AI coding assistants and other tools that support the MCP protocol, allowing them to generate diagrams without needing direct access to the Mermaid CLI.

## Features

- Generate diagrams from Mermaid syntax (flowcharts, sequence diagrams, class diagrams, etc.)
- Multiple output formats:
  - SVG: Vector graphics, ideal for web and scalable diagrams
  - PNG: Raster graphics, good for general use and compatibility
  - PDF: Document format, perfect for print and formal documentation
- Support for multiple themes (default, neutral, dark, forest, base)
- Customizable background colors (hex codes or named colors)
- Two operation modes (both available in STDIO and SSE transport):
  - File-based: Save diagrams to disk and return the path
  - Stream-based: Return base64-encoded diagram data (requires MCP client with image support)
- Comprehensive error handling and validation
- Detailed logging with configurable levels

## Prerequisites for Use

Before configuring your MCP client, ensure you have the following installed on your system:

- **Node.js**: Version 14 or higher.
- **Mermaid CLI**: Install globally using `npm install -g @mermaid-js/mermaid-cli`. This is required by the server to render diagrams.
- **UV Package Installer**: Install using `pip install uv`. This is used by `uvx` to run the server from PyPI.
- **Operating Systems**: Linux, macOS, Windows are supported.

## Configuring Your MCP Client (Recommended Method)

The easiest way to use this MCP server is by adding the following `uvx` configuration to your MCP client's JSON settings. This command will automatically download `mcp-mermaid-image-gen` from PyPI (if not already cached or installed) and run it in an isolated environment when your client calls it.

**Example: Claude Desktop Configuration**

To configure Claude Desktop, open its `claude_desktop_config.json` file (typically found in `~/Library/Application Support/Claude/` on macOS, `%APPDATA%\Claude\` on Windows, or `~/.config/Claude/` on Linux) and add the following to the `mcpServers` section:

```json
{
  "mcpServers": {
    "mermaid_image_generator": {
      "command": "uvx",
      "args": [
        "mcp_mermaid_image_gen"
      ]
    }
  }
}
```

After saving the configuration, restart your MCP client. The `mermaid_image_generator` toolset should now be available. The `mcp-mermaid-image-gen-server` in the `args` array is the command-line entry point defined by the package.

For other MCP clients, adapt the `command` and `args` to their specific MCP server registration format, using `uvx` and the `mcp-mermaid-image-gen-server` argument.

## Alternative Installation & Configuration Methods

While using `uvx` via client configuration is recommended, you might have reasons to install the server differently (e.g., for development).

### Installing from PyPI directly (Optional)

If you have a specific need to install the package into a particular Python environment (this is less common for MCP servers primarily used via `uvx`), you can use:
```bash
# Ensure UV is installed (e.g., pip install uv)
uv pip install mcp-mermaid-image-gen
```
This makes the `mcp_mermaid_image_gen-server` command available in that environment.

### Installing from Source (for Development/Contribution)

If you want to contribute to the server or run a modified version:

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp_mermaid_image_gen.git
cd mcp_mermaid_image_gen

# Create and activate a virtual environment using UV
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e .
```
This installs the server in editable mode within your local virtual environment.

### Configuring Client with Local Development Installation

If you have installed the server from source for development purposes, you can configure your client to point directly to the server script in your local virtual environment.

**Example: Claude Desktop (Local Development Setup)**

```json
{
  "mcpServers": {
    "mermaid_image_generator_dev": { // Use a different key for the dev version
      "command": "/path/to/your/mcp_mermaid_image_gen/.venv/bin/mcp_mermaid_image_gen-server"
    }
  }
}
```
Replace `/path/to/your/mcp_mermaid_image_gen/` with the absolute path to your project directory.

## Testing with MCP Inspector

The MCP SDK includes a development console (MCP Inspector) that allows you to test the server interactively. After installation, run:

```bash
mcp dev mcp_mermaid_image_gen/server/app.py
```

This will:
1. Start the MCP Inspector web interface
2. Allow testing via both STDIO and SSE transport modes
3. Provide a UI for calling the server's tools
4. Display returned images directly in the browser
5. Show detailed logs and debugging information

The Inspector is particularly useful for:
- Testing different diagram types
- Trying out various formats (SVG, PNG, PDF)
- Experimenting with themes and colors
- Debugging issues with Mermaid syntax
- Verifying both file and stream-based operation modes

## Available Tools

### generate_mermaid_diagram_file

Generates a Mermaid diagram and saves it to a local file.

Parameters:
- `code` (str): Mermaid diagram syntax
- `folder` (str): Output directory path
- `name` (str): Output filename (extension can determine format)
- `theme` (str, optional): Theme name (default, neutral, dark, forest, base)
- `backgroundColor` (str, optional): Background color (hex or named color)
- `format` (str, optional): Output format (svg, png, pdf). If not specified:
  1. Inferred from filename extension (e.g., "diagram.svg" -> svg)
  2. Defaults to "png" if no valid extension found

Returns: Path to the generated file

Format Selection Priority:
1. Explicit `format` parameter if provided
2. File extension in `name` parameter if valid
3. Defaults to PNG if neither is specified

### generate_mermaid_diagram_stream

Generates a Mermaid diagram and returns it directly as base64-encoded data. Requires an MCP client that supports handling image data (like the MCP Inspector).

Parameters:
- `code` (str): Mermaid diagram syntax
- `theme` (str, optional): Theme name (default, neutral, dark, forest, base)
- `backgroundColor` (str, optional): Background color (hex or named color)
- `format` (str, optional): Output format (svg, png, pdf). Defaults to "png"

Returns: Base64-encoded diagram data with appropriate MIME type:
- SVG: `image/svg+xml`
- PNG: `image/png`
- PDF: `application/pdf`

## Transport Modes

Both STDIO and SSE transport modes support all server functionality. The choice between them depends on your use case:

### STDIO Mode (Default)
- Synchronous operation
- Simple command-line integration
- Works with all tools and operation modes
- Ideal for scripts and command-line tools
- Example client: MCP Inspector, Cursor

### SSE Mode
- Asynchronous operation
- HTTP-based communication
- Works with all tools and operation modes
- Ideal for web applications and services
- Example client: MCP Inspector, web applications

## Client Compatibility

The server supports any MCP client, but some features require specific client capabilities:

1. File-based generation (`generate_mermaid_diagram_file`):
   - Requires client to have file system access
   - Works with all MCP clients
   - Client must be able to read the returned file path

2. Stream-based generation (`generate_mermaid_diagram_stream`):
   - Requires client capable of handling base64-encoded image data
   - Works with MCP Inspector and other image-capable clients
   - No file system access needed

The MCP Inspector (included with the MCP SDK) supports all features in both transport modes.

## Usage

The server provides two entry points:

1. `mcp_mermaid_image_gen-server`: The MCP server
   ```bash
   # Run with stdio transport (default)
   mcp_mermaid_image_gen-server

   # Run with SSE transport
   mcp_mermaid_image_gen-server --transport sse --port 3001
   ```

2. `mcp_mermaid_image_gen-client`: Test client (for development)
   ```bash
   mcp_mermaid_image_gen-client "your mermaid code here"
   ```

## Logging

The server logs all activity to both stderr and a rotating log file. Log files are stored in OS-specific locations:

- **macOS**: `~/Library/Logs/mcp-servers/mcp_mermaid_image_gen.log`
- **Linux**: 
  - Root user: `/var/log/mcp-servers/mcp_mermaid_image_gen.log`
  - Non-root: `~/.local/state/mcp-servers/logs/mcp_mermaid_image_gen.log`
- **Windows**: `%USERPROFILE%\AppData\Local\mcp-servers\logs\mcp_mermaid_image_gen.log`

Log files are automatically rotated when they reach 10MB, with up to 5 backup files kept.

Configure logging level with the `LOG_LEVEL` environment variable:
```bash
LOG_LEVEL=DEBUG mcp_mermaid_image_gen-server
```

Valid log levels: DEBUG, INFO (default), WARNING, ERROR, CRITICAL

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development instructions.

## Troubleshooting

Common issues and solutions:

1. **"mmdc command not found"**
   - Ensure Node.js is installed
   - Run `npm install -g @mermaid-js/mermaid-cli`
   - Verify `mmdc` is in your PATH

2. **"Transport mode not supported"**
   - For streaming mode, ensure you're using SSE transport
   - For file mode, either transport works

3. **"Directory not writable"**
   - Check folder permissions
   - For file mode, ensure the client has write access

4. **"Invalid format specified"**
   - Ensure format is one of: svg, png, pdf
   - Check for format/extension mismatch
   - Verify filename has valid extension if using extension-based format selection

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

Tim Kitchens (timkitch@codingthefuture.ai)

---

[Replace this example Echo server README with documentation specific to your MCP server. Use this structure as a template, but customize all sections to describe your server's actual functionality, tools, and configuration options.]
