"""Image extraction and handling utilities for Box Notes."""

import base64
import hashlib
import re
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse


def is_data_uri(url: str) -> bool:
    """
    Check if a URL is a data URI.

    Args:
        url: URL string to check

    Returns:
        True if URL is a data URI, False otherwise

    Examples:
        >>> is_data_uri("data:image/png;base64,iVBORw0KGgo=")
        True
        >>> is_data_uri("https://example.com/image.png")
        False
    """
    return url.startswith("data:")


def parse_data_uri(data_uri: str) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Parse a data URI into mime type and decoded data.

    Args:
        data_uri: Data URI string

    Returns:
        Tuple of (mime_type, data) or (None, None) if invalid

    Examples:
        >>> mime, data = parse_data_uri("data:image/png;base64,iVBORw0KGgo=")
        >>> mime
        'image/png'
        >>> isinstance(data, bytes)
        True
    """
    if not is_data_uri(data_uri):
        return None, None

    try:
        # Parse data URI format: data:[<mediatype>][;base64],<data>
        match = re.match(r"data:([^;,]+)?(?:;base64)?,(.+)", data_uri)
        if not match:
            return None, None

        mime_type = match.group(1) or "application/octet-stream"
        data_str = match.group(2)

        # Check if base64 encoded
        if ";base64" in data_uri:
            data = base64.b64decode(data_str)
        else:
            # URL-encoded data
            data = data_str.encode("utf-8")

        return mime_type, data

    except Exception:
        return None, None


def get_file_extension(mime_type: str) -> str:
    """
    Get file extension from MIME type.

    Args:
        mime_type: MIME type string

    Returns:
        File extension including dot (e.g., '.png')

    Examples:
        >>> get_file_extension("image/png")
        '.png'
        >>> get_file_extension("image/jpeg")
        '.jpg'
    """
    mime_to_ext = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
    }
    return mime_to_ext.get(mime_type.lower(), ".png")


def generate_image_filename(data: bytes, mime_type: str, prefix: str = "image") -> str:
    """
    Generate a unique filename for an image based on its content hash.

    Args:
        data: Image data bytes
        mime_type: MIME type of the image
        prefix: Prefix for the filename

    Returns:
        Filename string

    Examples:
        >>> data = b"test image data"
        >>> generate_image_filename(data, "image/png")
        'image_a94a8fe5ccb19ba61c4c0873d391e987982fbbd3.png'
    """
    # Create hash of image data for unique filename
    hash_obj = hashlib.sha1(data)
    hash_str = hash_obj.hexdigest()

    # Get extension from MIME type
    ext = get_file_extension(mime_type)

    return f"{prefix}_{hash_str}{ext}"


def extract_image(
    url: str, output_dir: Path, filename_prefix: str = "image"
) -> Optional[str]:
    """
    Extract an image from a URL or data URI and save it to a directory.

    Args:
        url: Image URL or data URI
        output_dir: Directory to save the image
        filename_prefix: Prefix for the generated filename

    Returns:
        Relative path to the saved image file, or None if extraction failed

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> tmpdir = Path(tempfile.mkdtemp())
        >>> data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        >>> path = extract_image(data_uri, tmpdir)
        >>> path is not None
        True
        >>> tmpdir.joinpath(path).exists()
        True
    """
    if not url:
        return None

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle data URIs
    if is_data_uri(url):
        mime_type, data = parse_data_uri(url)
        if not data:
            return None

        # Generate filename
        filename = generate_image_filename(
            data, mime_type or "image/png", filename_prefix
        )
        output_path = output_dir / filename

        # Write image data
        try:
            with open(output_path, "wb") as f:
                f.write(data)
            return filename
        except Exception:
            return None

    # Handle external URLs - save reference but don't download
    # Just return the URL as-is for external images
    return url


def get_image_dimensions(data: bytes) -> Optional[Tuple[int, int]]:
    """
    Get dimensions of an image from its data (basic PNG/JPEG support).

    Args:
        data: Image data bytes

    Returns:
        Tuple of (width, height) or None if unable to determine

    Note:
        This is a basic implementation. For full support, use PIL/Pillow.
    """
    try:
        # PNG signature and IHDR chunk
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            if data[12:16] == b"IHDR":
                width = int.from_bytes(data[16:20], "big")
                height = int.from_bytes(data[20:24], "big")
                return width, height

        # JPEG signature
        if data[:2] == b"\xff\xd8":
            # Very basic JPEG dimension extraction
            # In production, use PIL/Pillow instead
            return None

        return None
    except Exception:
        return None


def sanitize_image_url(url: str) -> str:
    """
    Sanitize an image URL for safe use.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL string

    Examples:
        >>> sanitize_image_url("javascript:alert(1)")
        ''
        >>> sanitize_image_url("https://example.com/image.png")
        'https://example.com/image.png'
    """
    if not url:
        return ""

    # Block dangerous protocols
    dangerous_protocols = ["javascript:", "data:text/html", "vbscript:"]
    url_lower = url.lower()

    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return ""

    # Allow data URIs for images only
    if url_lower.startswith("data:"):
        if not url_lower.startswith("data:image/"):
            return ""

    return url


def find_box_notes_images(boxnote_path: Path) -> Optional[Path]:
    """
    Find the Box Notes Images directory for a given .boxnote file.

    Box Notes stores images externally in:
    {parent_dir}/Box Notes Images/{note_name} Images/

    Args:
        boxnote_path: Path to the .boxnote file

    Returns:
        Path to the images directory if it exists, None otherwise

    Examples:
        >>> from pathlib import Path
        >>> # For: /path/MyNote.boxnote
        >>> # Looks for: /path/Box Notes Images/MyNote Images/
    """
    parent_dir = boxnote_path.parent
    note_name = boxnote_path.stem  # Filename without .boxnote extension

    # Box Notes naming pattern: "{note_name} Images"
    images_subdir = f"{note_name} Images"
    images_path = parent_dir / "Box Notes Images" / images_subdir

    if images_path.exists() and images_path.is_dir():
        return images_path

    return None


def copy_box_notes_images(
    boxnote_path: Path, output_images_dir: Path, verbose_callback=None
) -> List[str]:
    """
    Copy Box Notes external images to the output directory.

    Args:
        boxnote_path: Path to the .boxnote file
        output_images_dir: Directory to copy images to
        verbose_callback: Optional callback function for progress messages

    Returns:
        List of copied image filenames (relative paths)

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> # Copies all images from Box Notes Images directory
    """
    copied_files = []

    # Find the Box Notes Images directory
    source_images_dir = find_box_notes_images(boxnote_path)
    if not source_images_dir:
        return copied_files

    # Create output directory
    output_images_dir.mkdir(parents=True, exist_ok=True)

    # Copy all image files
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"}

    for image_file in source_images_dir.iterdir():
        if image_file.is_file() and image_file.suffix.lower() in image_extensions:
            dest_file = output_images_dir / image_file.name

            if verbose_callback:
                verbose_callback(f"Copying image: {image_file.name}")

            try:
                shutil.copy2(image_file, dest_file)
                copied_files.append(image_file.name)
            except Exception as e:
                if verbose_callback:
                    verbose_callback(f"Failed to copy {image_file.name}: {e}")

    return copied_files
