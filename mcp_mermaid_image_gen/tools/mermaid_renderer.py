import asyncio
import subprocess
import tempfile
import os
import logging
from typing import Optional, Tuple
import pathlib

logger = logging.getLogger(__name__)

VALID_THEMES = ["default", "neutral", "dark", "forest", "base"]
DEFAULT_MMDC_THEME = "default"

# Valid output formats supported by mmdc
VALID_FORMATS = ["svg", "png", "pdf"]
DEFAULT_FORMAT = "png"

def validate_and_normalize_format(name: str, format: Optional[str] = None) -> Tuple[str, str]:
    """
    Validate and normalize the output format based on filename extension and/or explicit format.
    
    Args:
        name: The output filename
        format: Optional explicit format (should be one of VALID_FORMATS if provided)
        
    Returns:
        Tuple[str, str]: (normalized_filename, format)
        
    Raises:
        ValueError: If format is invalid or conflicts with filename extension
    """
    # Extract extension from filename (without .png that might have been appended)
    name_base = name.lower()
    if name_base.endswith('.png'):
        name_base = name_base[:-4]
    file_ext = None
    for ext in VALID_FORMATS:
        if name_base.endswith(f'.{ext}'):
            file_ext = ext
            name_base = name_base[:-len(ext)-1]  # Remove the extension including dot
            break
    
    # Determine format
    if format and format.lower() not in VALID_FORMATS:
        raise ValueError(f"Invalid format '{format}'. Must be one of: {', '.join(VALID_FORMATS)}")
    
    if file_ext and format and file_ext != format.lower():
        raise ValueError(f"Format mismatch: filename extension '.{file_ext}' doesn't match specified format '{format}'")
    
    # Use explicit format if provided, otherwise use extension, or default to PNG
    final_format = format.lower() if format else (file_ext if file_ext else DEFAULT_FORMAT)
    final_name = f"{name_base}.{final_format}"
    
    return final_name, final_format

async def render_mermaid_to_file(
    code: str,
    output_dir: str,
    name: str,
    theme: Optional[str] = None,
    background_color: Optional[str] = None,
    format: Optional[str] = None,
) -> str:
    """
    Renders Mermaid code to an image file using the @mermaid-js/mermaid-cli (mmdc).

    Args:
        code: The Mermaid diagram code string.
        output_dir: Directory where the generated image should be saved.
        name: Name for the output file (extension determines format if format not specified).
        theme: The Mermaid theme to use (e.g., "default", "forest", "dark", "neutral").
        background_color: Background color for the diagram (e.g., "white", "transparent", "#F0F0F0").
        format: Output format ("svg", "png", or "pdf"). If not specified, inferred from filename or defaults to "png".

    Returns:
        str: The absolute path to the generated image file.

    Raises:
        ValueError: If mmdc fails to generate the diagram.
        ValueError: If an invalid theme or format is specified.
        ValueError: If filename extension conflicts with specified format.
        FileNotFoundError: If mmdc command is not found.
    """
    # Ensure output directory exists
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        raise ValueError(f"Output directory does not exist: {output_dir}")
    if not os.path.isdir(output_dir):
        raise ValueError(f"Output path is not a directory: {output_dir}")

    # Validate theme
    current_theme = theme if theme else DEFAULT_MMDC_THEME
    if current_theme not in VALID_THEMES:
        raise ValueError(
            f"Invalid theme: {current_theme}. Must be one of: {', '.join(VALID_THEMES)}"
        )

    # Validate and normalize format and filename
    normalized_name, output_format = validate_and_normalize_format(name, format)
    output_path = os.path.join(output_dir, normalized_name)

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".mmd", delete=False) as tmp_input_file:
        tmp_input_file_path = tmp_input_file.name
        tmp_input_file.write(code)
        tmp_input_file.flush()

    cmd = [
        "mmdc",
        "-i", tmp_input_file_path,
        "-o", output_path,
        "-t", current_theme,
        "-e", output_format,  # Explicitly specify output format
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