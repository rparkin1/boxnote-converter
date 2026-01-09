"""Format detection for Box Notes files."""

from typing import Any, Dict

from boxnotes.exceptions import UnsupportedFormatError
from boxnotes.models import FormatType


def detect_format(data: Dict[str, Any]) -> FormatType:
    """
    Detect Box Notes format from JSON data.

    Args:
        data: Parsed JSON data from Box Notes file

    Returns:
        FormatType.OLD for pre-August 2022 format
        FormatType.NEW for post-August 2022 format

    Raises:
        UnsupportedFormatError: If format cannot be determined

    Examples:
        >>> old_data = {"atext": {"text": "...", "attribs": "...", "pool": {}}}
        >>> detect_format(old_data)
        <FormatType.OLD: 'old'>

        >>> new_data = {"doc": {"type": "doc", "content": []}}
        >>> detect_format(new_data)
        <FormatType.NEW: 'new'>
    """
    if not isinstance(data, dict):
        raise UnsupportedFormatError("Box Notes data must be a dictionary")

    # Check for old format (pre-August 2022)
    # Old format has 'atext' key with nested 'text', 'attribs', 'pool'
    if "atext" in data:
        atext = data["atext"]
        if not isinstance(atext, dict):
            raise UnsupportedFormatError(
                "Old format 'atext' field must be a dictionary"
            )

        # Validate old format structure
        required_keys = {"text", "attribs"}
        if not required_keys.issubset(atext.keys()):
            raise UnsupportedFormatError(
                f"Old format missing required keys: {required_keys - set(atext.keys())}"
            )

        return FormatType.OLD

    # Check for new format (post-August 2022)
    # New format has 'doc' key with ProseMirror-like structure
    if "doc" in data:
        doc = data["doc"]
        if not isinstance(doc, dict):
            raise UnsupportedFormatError("New format 'doc' field must be a dictionary")

        # Validate new format structure
        if doc.get("type") != "doc":
            raise UnsupportedFormatError(
                f"New format 'doc.type' must be 'doc', got {doc.get('type')}"
            )

        if "content" not in doc:
            raise UnsupportedFormatError("New format 'doc' missing 'content' field")

        return FormatType.NEW

    # Check if data itself is a ProseMirror doc (alternative structure)
    if data.get("type") == "doc" and "content" in data:
        return FormatType.NEW

    # Unknown format
    raise UnsupportedFormatError(
        "Unknown Box Notes format. Expected 'atext' (old) or 'doc' (new) field."
    )


def validate_old_format(data: Dict[str, Any]) -> bool:
    """
    Validate old format Box Notes structure.

    Args:
        data: Parsed JSON data

    Returns:
        True if structure is valid

    Raises:
        UnsupportedFormatError: If structure is invalid
    """
    if "atext" not in data:
        raise UnsupportedFormatError("Old format missing 'atext' field")

    atext = data["atext"]
    if not isinstance(atext, dict):
        raise UnsupportedFormatError("'atext' must be a dictionary")

    if "text" not in atext or not isinstance(atext["text"], str):
        raise UnsupportedFormatError("'atext.text' must be a string")

    if "attribs" not in atext or not isinstance(atext["attribs"], str):
        raise UnsupportedFormatError("'atext.attribs' must be a string")

    # Pool is optional but should be dict if present
    if "pool" in atext and not isinstance(atext["pool"], dict):
        raise UnsupportedFormatError("'atext.pool' must be a dictionary")

    return True


def validate_new_format(data: Dict[str, Any]) -> bool:
    """
    Validate new format Box Notes structure.

    Args:
        data: Parsed JSON data

    Returns:
        True if structure is valid

    Raises:
        UnsupportedFormatError: If structure is invalid
    """
    # Handle both {"doc": {...}} and direct doc format
    doc = data.get("doc", data)

    if doc.get("type") != "doc":
        raise UnsupportedFormatError(
            f"New format 'type' must be 'doc', got {doc.get('type')}"
        )

    if "content" not in doc:
        raise UnsupportedFormatError("New format missing 'content' field")

    if not isinstance(doc["content"], list):
        raise UnsupportedFormatError("New format 'content' must be a list")

    return True
