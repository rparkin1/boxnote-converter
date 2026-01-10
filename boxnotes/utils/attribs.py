"""Attribute decompression utilities for old format Box Notes."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple


def decode_base36(value: str) -> int:
    """
    Decode a base-36 encoded string to an integer.

    Base-36 uses digits 0-9 and letters a-z (case-insensitive).

    Args:
        value: Base-36 encoded string

    Returns:
        Decoded integer value

    Examples:
        >>> decode_base36("0")
        0
        >>> decode_base36("a")
        10
        >>> decode_base36("z")
        35
        >>> decode_base36("10")
        36
    """
    try:
        return int(value, 36)
    except ValueError as e:
        raise ValueError(f"Invalid base-36 string: {value}") from e


@dataclass
class AttributeChunk:
    """
    A chunk of text with consistent attributes.

    Represents a span of characters with a set of formatting attributes
    applied, extracted from compressed attribute strings.
    """

    attributes: Set[int]  # Set of attribute pool indices
    num_characters: int  # Number of characters this applies to
    num_linebreaks: int = 0  # Number of line breaks after the characters

    def __post_init__(self) -> None:
        """Validate chunk."""
        if self.num_characters < 0:
            raise ValueError("num_characters must be non-negative")
        if self.num_linebreaks < 0:
            raise ValueError("num_linebreaks must be non-negative")


def parse_attribute_string(attrib_string: str) -> List[AttributeChunk]:
    """
    Parse compressed attribute string into chunks.

    The attribute string format is:
    - `*n`: Attribute index (base-36) from pool
    - `+m`: Number of characters (base-36)
    - `|k`: Number of line breaks (base-36)

    Pattern: `*n[*n...]+m[|k]` or `+m` (for chunks without attributes)

    Real example: "*4*5*6+a*4|2+2" means:
    - Chunk 1: attributes {4,5,6}, 10 chars
    - Chunk 2: attribute {4}, 0 chars, 2 linebreaks, then 2 more chars

    Args:
        attrib_string: Compressed attribute string from Box Notes

    Returns:
        List of AttributeChunk objects

    Raises:
        ValueError: If attribute string format is invalid
    """
    if not attrib_string:
        return []

    chunks: List[AttributeChunk] = []

    # Split chunks - a new chunk starts when we see:
    # - A '*' that follows a digit/letter (end of previous chunk's count)
    # - A '+' at the start (chunk with no attributes)
    # Use lookahead to split before * or + that starts a new chunk
    # But keep consecutive *s together (like *4*5*6)

    # Better approach: iterate character by character
    i = 0
    while i < len(attrib_string):
        # Skip to start of next chunk
        while i < len(attrib_string) and attrib_string[i] not in ("*", "+"):
            i += 1

        if i >= len(attrib_string):
            break

        # Found start of chunk, now find the end
        chunk_start = i
        attributes: Set[int] = set()

        # Parse attributes (consecutive * patterns)
        while i < len(attrib_string) and attrib_string[i] == "*":
            i += 1  # Skip the *
            # Extract attribute number (until we hit another * or +)
            num_str = ""
            while i < len(attrib_string) and attrib_string[i] not in ("*", "+", "|"):
                num_str += attrib_string[i]
                i += 1

            if num_str:
                try:
                    attributes.add(decode_base36(num_str))
                except ValueError:
                    pass

        # Now parse the count part (starts with +)
        num_chars = 0
        num_breaks = 0

        if i < len(attrib_string) and attrib_string[i] == "+":
            i += 1  # Skip the +
            # Extract character count (until we hit | or next chunk marker)
            count_str = ""
            while i < len(attrib_string) and attrib_string[i] not in ("|", "*", "+"):
                count_str += attrib_string[i]
                i += 1

            if count_str:
                try:
                    num_chars = decode_base36(count_str)
                except ValueError:
                    pass

        # Check for linebreaks (starts with |)
        if i < len(attrib_string) and attrib_string[i] == "|":
            i += 1  # Skip the |
            # Extract linebreak count (until we hit + or * which starts a new chunk)
            break_str = ""
            while i < len(attrib_string) and attrib_string[i] not in ("*", "+"):
                break_str += attrib_string[i]
                i += 1

            if break_str:
                try:
                    num_breaks = decode_base36(break_str)
                except ValueError:
                    pass

            # Note: A '+' after '|' starts a NEW chunk, so we don't consume it here

        # Create chunk
        if num_chars > 0 or num_breaks > 0:
            chunks.append(
                AttributeChunk(
                    attributes=attributes,
                    num_characters=num_chars,
                    num_linebreaks=num_breaks,
                )
            )

    return chunks


def resolve_attributes(
    pool_indices: Set[int], pool: Dict[str, Any]
) -> List[Tuple[str, str]]:
    """
    Resolve attribute pool indices to actual attribute names and values.

    Args:
        pool_indices: Set of pool indices to resolve
        pool: Attribute pool from Box Notes (numToAttrib mapping)

    Returns:
        List of (name, value) tuples

    Examples:
        >>> pool = {"0": ["bold", "true"], "1": ["font-size-medium", "true"]}
        >>> resolve_attributes({0, 1}, pool)
        [('bold', 'true'), ('font-size-medium', 'true')]
    """
    if not pool or "numToAttrib" not in pool:
        return []

    num_to_attrib = pool["numToAttrib"]
    attributes: List[Tuple[str, str]] = []

    for index in sorted(pool_indices):
        key = str(index)
        if key in num_to_attrib:
            attr_data = num_to_attrib[key]
            if isinstance(attr_data, list) and len(attr_data) >= 2:
                name, value = attr_data[0], attr_data[1]
                attributes.append((name, value))

    return attributes


def extract_text_spans(
    text: str, chunks: List[AttributeChunk], pool: Dict[str, Any]
) -> List[Tuple[str, List[Tuple[str, str]]]]:
    """
    Extract text spans with their resolved attributes.

    Args:
        text: Raw document text
        chunks: List of attribute chunks
        pool: Attribute pool

    Returns:
        List of (text_content, attributes) tuples

    Examples:
        >>> text = "Hello world"
        >>> chunks = [AttributeChunk({0}, 5, 0), AttributeChunk({1}, 6, 0)]
        >>> pool = {"numToAttrib": {"0": ["bold", "true"], "1": ["italic", "true"]}}
        >>> extract_text_spans(text, chunks, pool)
        [('Hello', [('bold', 'true')]), (' world', [('italic', 'true')])]
    """
    spans: List[Tuple[str, List[Tuple[str, str]]]] = []
    position = 0

    for chunk in chunks:
        # Extract text for this chunk
        if chunk.num_characters > 0:
            end_pos = min(position + chunk.num_characters, len(text))
            text_content = text[position:end_pos]
            position = end_pos

            # Resolve attributes
            attributes = resolve_attributes(chunk.attributes, pool)

            # Add span
            if text_content or attributes:
                spans.append((text_content, attributes))

        # Handle line breaks
        if chunk.num_linebreaks > 0:
            # Add linebreaks to the text
            linebreaks = "\n" * chunk.num_linebreaks
            position = min(position + chunk.num_linebreaks, len(text))
            spans.append((linebreaks, []))

    return spans


def detect_block_type(attributes: List[Tuple[str, str]]) -> str:
    """
    Detect block type from attributes.

    Args:
        attributes: List of (name, value) tuples

    Returns:
        Block type string (e.g., 'heading', 'list', 'paragraph')

    Examples:
        >>> detect_block_type([('heading', 'h1')])
        'heading'
        >>> detect_block_type([('list', 'number1')])
        'list'
        >>> detect_block_type([('bold', 'true')])
        'paragraph'
    """
    for name, value in attributes:
        # Check for heading
        if name == "heading" or name.startswith("heading"):
            return "heading"

        # Check for list
        if name == "list" or name.startswith("list"):
            return "list"

        # Check for code block
        if name == "code" or name == "codeblock":
            return "code_block"

        # Check for blockquote
        if name == "blockquote" or name == "quote":
            return "blockquote"

    # Default to paragraph
    return "paragraph"
