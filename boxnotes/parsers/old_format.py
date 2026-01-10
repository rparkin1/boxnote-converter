"""Parser for old format Box Notes (pre-August 2022)."""

from typing import Any, Dict, List, Tuple

from boxnotes.exceptions import ParsingError
from boxnotes.models import (
    Block,
    BlockType,
    Document,
    ListType,
    TextAttributes,
    TextSpan,
)
from boxnotes.parsers.base import BoxNoteParser
from boxnotes.utils.attribs import (
    extract_text_spans,
    parse_attribute_string,
    resolve_attributes,
)


class OldFormatParser(BoxNoteParser):
    """
    Parser for old format Box Notes (created before August 2022).

    Old format uses the 'atext' structure with compressed attribute strings
    that must be decompressed to reconstruct the document.
    """

    def parse(self, data: Dict[str, Any]) -> Document:
        """
        Parse old format Box Notes data into a Document.

        Args:
            data: Parsed JSON data from Box Notes file

        Returns:
            Document object with parsed content

        Raises:
            ParsingError: If parsing fails
        """
        try:
            # Extract atext components
            if "atext" not in data:
                raise ParsingError("Old format missing 'atext' field")

            atext = data["atext"]
            text = atext.get("text", "")
            attribs = atext.get("attribs", "")
            pool = data.get("pool", {})

            # Parse attribute string into chunks
            chunks = parse_attribute_string(attribs)

            # Extract text spans with resolved attributes
            spans = extract_text_spans(text, chunks, pool)

            # Convert spans to Document blocks
            document = self._spans_to_document(spans)

            # Add metadata
            if "head" in data:
                document.metadata["revision"] = data["head"]
            if "lastEditTimestamp" in data:
                document.metadata["last_edit"] = data["lastEditTimestamp"]
            if "authorList" in data:
                document.metadata["authors"] = data["authorList"]

            return document

        except Exception as e:
            raise ParsingError(f"Failed to parse old format Box Notes: {e}") from e

    def _spans_to_document(
        self, spans: List[Tuple[str, List[Tuple[str, str]]]]
    ) -> Document:
        """
        Convert text spans with attributes to a Document.

        Args:
            spans: List of (text, attributes) tuples

        Returns:
            Document with blocks
        """
        blocks: List[Block] = []
        current_block: List[TextSpan] = []
        current_block_type = BlockType.PARAGRAPH
        current_block_attrs: Dict[str, Any] = {}

        for text_content, attributes in spans:
            # Handle linebreaks - they separate blocks
            if text_content == "\n" or (text_content and text_content[0] == "\n"):
                # Finish current block if it has content
                if current_block:
                    block = self._create_block(
                        current_block_type, current_block, current_block_attrs
                    )
                    if block:
                        blocks.append(block)
                    current_block = []
                    current_block_type = BlockType.PARAGRAPH
                    current_block_attrs = {}

                # Handle multiple newlines
                if len(text_content) > 1:
                    remaining = text_content[1:]
                    if remaining:
                        # Add remaining text to new block
                        text_attrs = self._attributes_to_text_attributes(attributes)
                        current_block.append(TextSpan(remaining, text_attrs))
                continue

            # Detect block type from attributes
            if attributes:
                block_type = self._detect_block_type(attributes)
                if block_type != current_block_type and current_block:
                    # Block type changed, start new block
                    block = self._create_block(
                        current_block_type, current_block, current_block_attrs
                    )
                    if block:
                        blocks.append(block)
                    current_block = []
                    current_block_attrs = {}

                current_block_type = block_type
                current_block_attrs = dict(attributes)

            # Convert attributes to TextAttributes
            text_attrs = self._attributes_to_text_attributes(attributes)

            # Add text span to current block
            if text_content:
                current_block.append(TextSpan(text_content, text_attrs))

        # Add final block if any content remains
        if current_block:
            block = self._create_block(
                current_block_type, current_block, current_block_attrs
            )
            if block:
                blocks.append(block)

        return Document(blocks=blocks)

    def _detect_block_type(self, attributes: List[Tuple[str, str]]) -> BlockType:
        """
        Detect block type from attributes.

        Args:
            attributes: List of (name, value) tuples

        Returns:
            BlockType
        """
        for name, value in attributes:
            name_lower = name.lower()

            # Check for heading
            if (
                "heading" in name_lower
                or name_lower.startswith("h")
                and name_lower[1:].isdigit()
            ):
                return BlockType.HEADING

            # Check for list
            if "list" in name_lower:
                return BlockType.LIST

            # Check for code block
            if "code" in name_lower:
                return BlockType.CODE_BLOCK

            # Check for blockquote
            if "quote" in name_lower or "blockquote" in name_lower:
                return BlockType.BLOCKQUOTE

        return BlockType.PARAGRAPH

    def _attributes_to_text_attributes(
        self, attributes: List[Tuple[str, str]]
    ) -> TextAttributes:
        """
        Convert attribute list to TextAttributes.

        Args:
            attributes: List of (name, value) tuples

        Returns:
            TextAttributes object
        """
        attrs = TextAttributes()

        for name, value in attributes:
            name_lower = name.lower()

            # Text formatting
            if name_lower == "bold" or name_lower == "b":
                attrs.bold = value.lower() == "true"
            elif name_lower == "italic" or name_lower == "i":
                attrs.italic = value.lower() == "true"
            elif name_lower == "code":
                attrs.code = value.lower() == "true"
            elif name_lower == "underline" or name_lower == "u":
                attrs.underline = value.lower() == "true"
            elif name_lower == "strike" or name_lower == "strikethrough":
                attrs.strike = value.lower() == "true"

            # Link
            elif name_lower == "link" or name_lower == "url":
                attrs.link = value

            # Font properties
            elif "font-color" in name_lower or "color" in name_lower:
                attrs.color = value
            elif "font-size" in name_lower or "size" in name_lower:
                attrs.size = value

            # Highlighting
            elif "highlight" in name_lower or "background" in name_lower:
                attrs.highlight = value

        return attrs

    def _create_block(
        self,
        block_type: BlockType,
        content: List[TextSpan],
        attributes: Dict[str, Any],
    ) -> Block:
        """
        Create a Block from content and attributes.

        Args:
            block_type: Type of block to create
            content: List of TextSpan objects
            attributes: Block attributes

        Returns:
            Block object or None if no valid content
        """
        if not content:
            return None

        # Handle different block types
        if block_type == BlockType.HEADING:
            # Determine heading level from attributes
            level = self._extract_heading_level(attributes)
            return Block(
                type=BlockType.HEADING,
                content=content,
                heading_level=level,
                attributes=attributes,
            )

        elif block_type == BlockType.LIST:
            # Determine list type from attributes
            list_type = self._extract_list_type(attributes)
            return Block(
                type=BlockType.LIST, list_type=list_type, attributes=attributes
            )

        else:
            # Standard block (paragraph, code, blockquote, etc.)
            return Block(type=block_type, content=content, attributes=attributes)

    def _extract_heading_level(self, attributes: Dict[str, Any]) -> int:
        """
        Extract heading level from attributes.

        Args:
            attributes: Block attributes

        Returns:
            Heading level (1, 2, or 3), defaults to 1
        """
        for name, value in attributes.items():
            name_lower = name.lower()
            value_lower = str(value).lower()

            if "heading" in name_lower or name_lower.startswith("h"):
                # Try to extract number from value or name
                for char in value_lower + name_lower:
                    if char.isdigit():
                        level = int(char)
                        if 1 <= level <= 3:
                            return level

        return 1  # Default to h1

    def _extract_list_type(self, attributes: Dict[str, Any]) -> ListType:
        """
        Extract list type from attributes.

        Args:
            attributes: Block attributes

        Returns:
            ListType
        """
        for name, value in attributes.items():
            name_lower = name.lower()
            value_lower = str(value).lower()

            if "list" in name_lower:
                # Check value for list type
                if "bullet" in value_lower or "unordered" in value_lower:
                    return ListType.BULLET
                elif "number" in value_lower or "ordered" in value_lower:
                    return ListType.ORDERED
                elif "check" in value_lower or "task" in value_lower:
                    return ListType.CHECK

        return ListType.BULLET  # Default to bullet list
