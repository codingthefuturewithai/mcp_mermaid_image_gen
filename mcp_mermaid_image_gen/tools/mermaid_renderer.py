import asyncio
import subprocess
import tempfile
import os
import logging
from typing import Optional
import pathlib

logger = logging.getLogger(__name__)

DEFAULT_MMDC_THEME = "default"

async def render_mermaid_to_file(
    code: str,
    output_dir: str,
    name: str,
    theme: Optional[str] = None,
    background_color: Optional[str] = None,
) -> str:
    """
    Renders Mermaid code to an image file using the @mermaid-js/mermaid-cli (mmdc).

    Args:
        code: The Mermaid diagram code string.
        output_dir: Directory where the generated image should be saved.
        name: Name for the output file (will be appended with .png if not included).
        theme: The Mermaid theme to use (e.g., "default", "forest", "dark", "neutral").
        background_color: Background color for the diagram (e.g., "white", "transparent", "#F0F0F0").

    Returns:
        str: The absolute path to the generated image file.

    Raises:
        ValueError: If mmdc fails to generate the diagram.
        FileNotFoundError: If mmdc command is not found.
    """
    # Ensure output directory exists
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        raise ValueError(f"Output directory does not exist: {output_dir}")
    if not os.path.isdir(output_dir):
        raise ValueError(f"Output path is not a directory: {output_dir}")

    # Ensure name has .png extension
    if not name.lower().endswith('.png'):
        name = f"{name}.png"

    # Construct full output path
    output_path = os.path.join(output_dir, name)

    # Use provided theme or default
    current_theme = theme if theme else DEFAULT_MMDC_THEME

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".mmd", delete=False) as tmp_input_file:
        tmp_input_file_path = tmp_input_file.name
        tmp_input_file.write(code)
        tmp_input_file.flush()

    cmd = [
        "mmdc",
        "-i", tmp_input_file_path,
        "-o", output_path,
        "-t", current_theme,
    ]

    if background_color:
        cmd.extend(["-b", background_color])

    logger.debug(f"Executing mmdc command: {' '.join(cmd)}")

    try:
        process = await asyncio.to_thread(
            subprocess.run,
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Mermaid diagram successfully generated: {output_path}")
        logger.debug(f"mmdc stdout: {process.stdout}")
        if process.stderr: # mmdc might output warnings to stderr on success
            logger.warning(f"mmdc stderr (on success): {process.stderr}")

    except FileNotFoundError:
        logger.error("mmdc command not found. Ensure @mermaid-js/mermaid-cli is installed and in PATH within the Docker image.")
        # This is a server configuration error, so reraise
        raise 
    except subprocess.CalledProcessError as e:
        error_message = (
            f"mmdc failed to generate diagram. Return code: {e.returncode}\n"
            f"Stdout: {e.stdout}\n"
            f"Stderr: {e.stderr}"
        )
        logger.error(error_message)
        raise ValueError(error_message) from e
    finally:
        if os.path.exists(tmp_input_file_path):
            os.remove(tmp_input_file_path)
            logger.debug(f"Removed temporary Mermaid input file: {tmp_input_file_path}")

    return output_path 