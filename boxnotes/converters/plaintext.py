"""Plain text converter for Box Notes documents."""

from typing import List

from boxnotes.converters.base import DocumentConverter
from boxnotes.exceptions import ConversionError
from boxnotes.models import Block, BlockType, Document, ListType, TextSpan


class PlainTextConverter(DocumentConverter):
    """
    Convert Box Notes documents to plain text format.

    Produces clean, readable text without markup syntax.
    """

    def convert(self, document: Document) -> str:
        """
        Convert a Document to plain text.

        Args:
            document: Document to convert

        Returns:
            Plain text string

        Raises:
            ConversionError: If conversion fails
        """
        try:
            lines: List[str] = []

            for block in document.blocks:
                text = self._convert_block(block)
                if text:
                    lines.append(text)

            # Join with double newlines for block separation
            return "\n\n".join(lines)

        except Exception as e:
            raise ConversionError(f"Failed to convert to plain text: {e}") from e

    def _convert_block(self, block: Block, indent_level: int = 0) -> str:
        """
        Convert a single block to plain text.

        Args:
            block: Block to convert
            indent_level: Current indentation level (for nested lists)

        Returns:
            Plain text string
        """
        if block.type == BlockType.PARAGRAPH:
            return self._convert_paragraph(block)
        elif block.type == BlockType.HEADING:
            return self._convert_heading(block)
        elif block.type == BlockType.CODE_BLOCK:
            return self._convert_code_block(block)
        elif block.type == BlockType.BLOCKQUOTE:
            return self._convert_blockquote(block)
        elif block.type == BlockType.HORIZONTAL_RULE:
            return "-" * 60
        elif block.type == BlockType.LIST:
            return self._convert_list(block, indent_level)
        elif block.type == BlockType.TABLE:
            return self._convert_table(block)
        elif block.type == BlockType.IMAGE:
            return self._convert_image(block)
        else:
            # Unknown block type, convert as paragraph
            return self._convert_paragraph(block)

    def _convert_paragraph(self, block: Block) -> str:
        """Convert paragraph block to plain text."""
        return self._convert_text_spans(block.content)

    def _convert_heading(self, block: Block) -> str:
        """Convert heading block to plain text with underline."""
        text = self._convert_text_spans(block.content)
        level = block.heading_level or 1

        # Use different underline styles for different levels
        if level == 1:
            underline = "=" * len(text)
        elif level == 2:
            underline = "-" * len(text)
        else:
            underline = "~" * len(text)

        return f"{text}\n{underline}"

    def _convert_code_block(self, block: Block) -> str:
        """Convert code block to plain text with indentation."""
        text = self._convert_text_spans(block.content)
        # Indent code blocks with 4 spaces
        lines = text.split("\n")
        return "\n".join(f"    {line}" for line in lines)

    def _convert_blockquote(self, block: Block) -> str:
        """Convert blockquote to plain text with indentation and prefix."""
        text = self._convert_text_spans(block.content)
        # Indent and add > prefix
        lines = text.split("\n")
        return "\n".join(f"    > {line}" for line in lines)

    def _convert_image(self, block: Block) -> str:
        """Convert image block to plain text."""
        # Get image attributes
        url = block.image_path or block.image_url or ""
        alt = block.image_alt or "image"

        # Plain text representation: [Image: alt] (url)
        return f"[Image: {alt}] ({url})"

    def _convert_list(self, block: Block, indent_level: int = 0) -> str:
        """Convert list block to plain text."""
        lines: List[str] = []
        indent = "  " * indent_level

        for i, item in enumerate(block.children, 1):
            if item.type == BlockType.LIST_ITEM:
                # Determine bullet/number based on list type
                if block.list_type == ListType.BULLET:
                    prefix = f"{indent}• "
                elif block.list_type == ListType.ORDERED:
                    prefix = f"{indent}{i}. "
                elif block.list_type == ListType.CHECK:
                    checked = "☑" if item.checked else "☐"
                    prefix = f"{indent}{checked} "
                else:
                    prefix = f"{indent}• "

                # Convert item content
                text = self._convert_text_spans(item.content)
                lines.append(f"{prefix}{text}")

                # Handle nested lists
                for child in item.children:
                    if child.type == BlockType.LIST:
                        nested = self._convert_list(child, indent_level + 1)
                        lines.append(nested)

        return "\n".join(lines)

    def _convert_table(self, block: Block) -> str:
        """Convert table to plain text with tab separation."""
        lines: List[str] = []

        for row in block.children:
            if row.type == BlockType.TABLE_ROW:
                # Convert each cell
                cells: List[str] = []
                for cell in row.children:
                    if cell.type == BlockType.TABLE_CELL:
                        cell_text = self._convert_text_spans(cell.content)
                        # Remove newlines from cells
                        cell_text = cell_text.replace("\n", " ")
                        cells.append(cell_text)

                # Create tab-separated row
                row_text = "\t".join(cells)
                lines.append(row_text)

        return "\n".join(lines)

    def _convert_text_spans(self, spans: List[TextSpan]) -> str:
        """
        Convert text spans to plain text.

        Args:
            spans: List of TextSpan objects

        Returns:
            Plain text string (all formatting removed)
        """
        parts: List[str] = []

        for span in spans:
            text = span.text

            # For links, show URL in parentheses after text
            if span.attributes.link:
                text = f"{text} ({span.attributes.link})"

            parts.append(text)

        return "".join(parts)
