"""Markdown converter for Box Notes documents."""

import re
from typing import List

from boxnotes.converters.base import DocumentConverter
from boxnotes.exceptions import ConversionError
from boxnotes.models import Block, BlockType, Document, ListType, TextSpan


class MarkdownConverter(DocumentConverter):
    """
    Convert Box Notes documents to Markdown format.

    Supports GitHub Flavored Markdown (GFM) including tables.
    """

    def convert(self, document: Document) -> str:
        """
        Convert a Document to Markdown.

        Args:
            document: Document to convert

        Returns:
            Markdown string

        Raises:
            ConversionError: If conversion fails
        """
        try:
            lines: List[str] = []

            for block in document.blocks:
                markdown = self._convert_block(block)
                if markdown:
                    lines.append(markdown)

            # Join with double newlines for block separation
            return "\n\n".join(lines)

        except Exception as e:
            raise ConversionError(f"Failed to convert to Markdown: {e}") from e

    def _convert_block(self, block: Block, indent_level: int = 0) -> str:
        """
        Convert a single block to Markdown.

        Args:
            block: Block to convert
            indent_level: Current indentation level (for nested lists)

        Returns:
            Markdown string
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
            return "---"
        elif block.type == BlockType.LIST:
            return self._convert_list(block, indent_level)
        elif block.type == BlockType.TABLE:
            return self._convert_table(block)
        else:
            # Unknown block type, convert as paragraph
            return self._convert_paragraph(block)

    def _convert_paragraph(self, block: Block) -> str:
        """Convert paragraph block to Markdown."""
        return self._convert_text_spans(block.content)

    def _convert_heading(self, block: Block) -> str:
        """Convert heading block to Markdown."""
        level = block.heading_level or 1
        prefix = "#" * level
        text = self._convert_text_spans(block.content)
        return f"{prefix} {text}"

    def _convert_code_block(self, block: Block) -> str:
        """Convert code block to Markdown."""
        text = self._convert_text_spans(block.content, preserve_formatting=False)
        # Use triple backticks for code blocks
        return f"```\n{text}\n```"

    def _convert_blockquote(self, block: Block) -> str:
        """Convert blockquote to Markdown."""
        text = self._convert_text_spans(block.content)
        # Add > prefix to each line
        lines = text.split("\n")
        return "\n".join(f"> {line}" for line in lines)

    def _convert_list(self, block: Block, indent_level: int = 0) -> str:
        """Convert list block to Markdown."""
        lines: List[str] = []
        indent = "  " * indent_level

        for i, item in enumerate(block.children, 1):
            if item.type == BlockType.LIST_ITEM:
                # Determine bullet/number based on list type
                if block.list_type == ListType.BULLET:
                    prefix = f"{indent}- "
                elif block.list_type == ListType.ORDERED:
                    prefix = f"{indent}{i}. "
                elif block.list_type == ListType.CHECK:
                    checked = "x" if item.checked else " "
                    prefix = f"{indent}- [{checked}] "
                else:
                    prefix = f"{indent}- "

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
        """Convert table to GitHub Flavored Markdown."""
        lines: List[str] = []

        for i, row in enumerate(block.children):
            if row.type == BlockType.TABLE_ROW:
                # Convert each cell
                cells: List[str] = []
                for cell in row.children:
                    if cell.type == BlockType.TABLE_CELL:
                        cell_text = self._convert_text_spans(cell.content)
                        # Escape pipe characters in cell content
                        cell_text = cell_text.replace("|", "\\|")
                        cells.append(cell_text)

                # Create table row
                row_text = "| " + " | ".join(cells) + " |"
                lines.append(row_text)

                # Add header separator after first row
                if i == 0:
                    separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                    lines.append(separator)

        return "\n".join(lines)

    def _convert_text_spans(
        self, spans: List[TextSpan], preserve_formatting: bool = True
    ) -> str:
        """
        Convert text spans to Markdown with inline formatting.

        Args:
            spans: List of TextSpan objects
            preserve_formatting: Whether to preserve formatting (False for code blocks)

        Returns:
            Formatted Markdown string
        """
        parts: List[str] = []

        for span in spans:
            text = span.text

            if not preserve_formatting:
                # Just return plain text
                parts.append(text)
                continue

            # Apply formatting marks
            if span.attributes.bold and span.attributes.italic:
                text = f"***{text}***"
            elif span.attributes.bold:
                text = f"**{text}**"
            elif span.attributes.italic:
                text = f"*{text}*"

            if span.attributes.code:
                text = f"`{text}`"

            if span.attributes.strike:
                text = f"~~{text}~~"

            if span.attributes.link:
                # Escape any ] in the text
                escaped_text = text.replace("]", "\\]")
                text = f"[{escaped_text}]({span.attributes.link})"

            # Escape special Markdown characters (except in code or links)
            if not span.attributes.code and not span.attributes.link:
                text = self._escape_markdown(text)

            parts.append(text)

        return "".join(parts)

    def _escape_markdown(self, text: str) -> str:
        """
        Escape special Markdown characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        # Don't escape if already formatted
        if text.startswith("**") or text.startswith("*") or text.startswith("`"):
            return text

        # Escape special characters that aren't already part of formatting
        # Be careful not to double-escape
        special_chars = ["\\", "#", "*", "_", "[", "]", "(", ")", "`"]

        for char in special_chars:
            # Only escape if not already escaped
            text = re.sub(f"(?<!\\\\){re.escape(char)}", f"\\{char}", text)

        return text
