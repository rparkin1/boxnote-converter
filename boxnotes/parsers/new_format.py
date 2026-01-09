"""Parser for new format Box Notes (post-August 2022)."""

from typing import Any, Dict, List, Optional

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


class NewFormatParser(BoxNoteParser):
    """
    Parser for new format Box Notes (created after August 2022).

    New format uses a ProseMirror-like JSON structure with nested content arrays.
    """

    def parse(self, data: Dict[str, Any]) -> Document:
        """
        Parse new format Box Notes data into a Document.

        Args:
            data: Parsed JSON data from Box Notes file

        Returns:
            Document object with parsed content

        Raises:
            ParsingError: If parsing fails
        """
        try:
            # Extract doc structure
            doc = data.get("doc", data)  # Handle both {"doc": {...}} and direct format

            if doc.get("type") != "doc":
                raise ParsingError(f"Expected doc type, got {doc.get('type')}")

            content = doc.get("content", [])

            # Parse content nodes into blocks
            blocks = self._parse_content_nodes(content)

            # Create document
            document = Document(blocks=blocks)

            # Add metadata
            if "version" in data:
                document.metadata["version"] = data["version"]
            if "schema_version" in data:
                document.metadata["schema_version"] = data["schema_version"]
            if "last_edit_timestamp" in data:
                document.metadata["last_edit"] = data["last_edit_timestamp"]

            return document

        except Exception as e:
            raise ParsingError(f"Failed to parse new format Box Notes: {e}") from e

    def _parse_content_nodes(self, nodes: List[Dict[str, Any]]) -> List[Block]:
        """
        Parse content nodes into blocks.

        Args:
            nodes: List of content node dictionaries

        Returns:
            List of Block objects
        """
        blocks: List[Block] = []

        for node in nodes:
            block = self._parse_node(node)
            if block:
                blocks.append(block)

        return blocks

    def _parse_node(self, node: Dict[str, Any]) -> Optional[Block]:
        """
        Parse a single node into a Block.

        Args:
            node: Node dictionary

        Returns:
            Block object or None
        """
        node_type = node.get("type")

        if not node_type:
            return None

        # Map node types to handlers
        if node_type == "paragraph":
            return self._parse_paragraph(node)
        elif node_type == "heading":
            return self._parse_heading(node)
        elif node_type == "code_block":
            return self._parse_code_block(node)
        elif node_type == "blockquote":
            return self._parse_blockquote(node)
        elif node_type == "horizontal_rule":
            return self._parse_horizontal_rule(node)
        elif node_type == "bullet_list":
            return self._parse_list(node, ListType.BULLET)
        elif node_type == "ordered_list":
            return self._parse_list(node, ListType.ORDERED)
        elif node_type == "check_list":
            return self._parse_list(node, ListType.CHECK)
        elif node_type == "table":
            return self._parse_table(node)

        # Unknown node type - return None
        return None

    def _parse_paragraph(self, node: Dict[str, Any]) -> Block:
        """Parse a paragraph node."""
        content = self._parse_inline_content(node.get("content", []))
        return Block(
            type=BlockType.PARAGRAPH,
            content=content,
            attributes=node.get("attrs", {})
        )

    def _parse_heading(self, node: Dict[str, Any]) -> Block:
        """Parse a heading node."""
        content = self._parse_inline_content(node.get("content", []))
        attrs = node.get("attrs", {})
        level = attrs.get("level", 1)

        # Ensure level is 1, 2, or 3
        if level not in (1, 2, 3):
            level = 1

        return Block(
            type=BlockType.HEADING,
            content=content,
            heading_level=level,
            attributes=attrs
        )

    def _parse_code_block(self, node: Dict[str, Any]) -> Block:
        """Parse a code block node."""
        content = self._parse_inline_content(node.get("content", []))
        return Block(
            type=BlockType.CODE_BLOCK,
            content=content,
            attributes=node.get("attrs", {})
        )

    def _parse_blockquote(self, node: Dict[str, Any]) -> Block:
        """Parse a blockquote node."""
        content = self._parse_inline_content(node.get("content", []))
        return Block(
            type=BlockType.BLOCKQUOTE,
            content=content,
            attributes=node.get("attrs", {})
        )

    def _parse_horizontal_rule(self, node: Dict[str, Any]) -> Block:
        """Parse a horizontal rule node."""
        return Block(
            type=BlockType.HORIZONTAL_RULE,
            content=[],
            attributes=node.get("attrs", {})
        )

    def _parse_list(self, node: Dict[str, Any], list_type: ListType) -> Block:
        """Parse a list node."""
        # Parse list items as children
        children = []
        for child_node in node.get("content", []):
            if child_node.get("type") in ("list_item", "check_list_item"):
                child_block = self._parse_list_item(child_node, list_type)
                if child_block:
                    children.append(child_block)

        return Block(
            type=BlockType.LIST,
            list_type=list_type,
            children=children,
            attributes=node.get("attrs", {})
        )

    def _parse_list_item(
        self, node: Dict[str, Any], list_type: ListType
    ) -> Optional[Block]:
        """Parse a list item node."""
        # List items can contain paragraphs or other content
        content_nodes = node.get("content", [])

        # Combine all text from nested paragraphs
        all_content: List[TextSpan] = []
        for content_node in content_nodes:
            if content_node.get("type") == "paragraph":
                all_content.extend(
                    self._parse_inline_content(content_node.get("content", []))
                )

        # Check if it's a check list item
        checked = None
        if node.get("type") == "check_list_item":
            attrs = node.get("attrs", {})
            checked = attrs.get("checked", False)

        return Block(
            type=BlockType.LIST_ITEM,
            content=all_content,
            checked=checked,
            attributes=node.get("attrs", {})
        )

    def _parse_table(self, node: Dict[str, Any]) -> Block:
        """Parse a table node."""
        # Tables have rows as children
        children = []
        for row_node in node.get("content", []):
            if row_node.get("type") == "table_row":
                row_block = self._parse_table_row(row_node)
                if row_block:
                    children.append(row_block)

        return Block(
            type=BlockType.TABLE,
            children=children,
            attributes=node.get("attrs", {})
        )

    def _parse_table_row(self, node: Dict[str, Any]) -> Optional[Block]:
        """Parse a table row node."""
        # Rows have cells as children
        children = []
        for cell_node in node.get("content", []):
            if cell_node.get("type") in ("table_cell", "table_header"):
                cell_block = self._parse_table_cell(cell_node)
                if cell_block:
                    children.append(cell_block)

        return Block(
            type=BlockType.TABLE_ROW,
            children=children,
            attributes=node.get("attrs", {})
        )

    def _parse_table_cell(self, node: Dict[str, Any]) -> Optional[Block]:
        """Parse a table cell node."""
        # Cells contain paragraphs or other content
        content_nodes = node.get("content", [])

        # Combine all text from nested content
        all_content: List[TextSpan] = []
        for content_node in content_nodes:
            if content_node.get("type") == "paragraph":
                all_content.extend(
                    self._parse_inline_content(content_node.get("content", []))
                )

        return Block(
            type=BlockType.TABLE_CELL,
            content=all_content,
            attributes=node.get("attrs", {})
        )

    def _parse_inline_content(
        self, content: List[Dict[str, Any]]
    ) -> List[TextSpan]:
        """
        Parse inline content (text nodes with marks).

        Args:
            content: List of inline content nodes

        Returns:
            List of TextSpan objects
        """
        spans: List[TextSpan] = []

        for node in content:
            node_type = node.get("type")

            if node_type == "text":
                text = node.get("text", "")
                marks = node.get("marks", [])
                attrs = self._marks_to_attributes(marks)

                if text:
                    spans.append(TextSpan(text=text, attributes=attrs))

            elif node_type == "hard_break":
                spans.append(TextSpan(text="\n", attributes=TextAttributes()))

        return spans

    def _marks_to_attributes(self, marks: List[Dict[str, Any]]) -> TextAttributes:
        """
        Convert ProseMirror marks to TextAttributes.

        Args:
            marks: List of mark dictionaries

        Returns:
            TextAttributes object
        """
        attrs = TextAttributes()

        for mark in marks:
            mark_type = mark.get("type")
            mark_attrs = mark.get("attrs", {})

            # Text formatting marks
            if mark_type == "strong" or mark_type == "bold":
                attrs.bold = True
            elif mark_type == "em" or mark_type == "italic":
                attrs.italic = True
            elif mark_type == "code":
                attrs.code = True
            elif mark_type == "underline":
                attrs.underline = True
            elif mark_type == "strike" or mark_type == "strikethrough":
                attrs.strike = True

            # Link mark
            elif mark_type == "link":
                attrs.link = mark_attrs.get("href")

            # Font properties
            elif mark_type == "font_color":
                attrs.color = mark_attrs.get("color")
            elif mark_type == "font_size":
                attrs.size = mark_attrs.get("size")
            elif mark_type == "highlight":
                attrs.highlight = mark_attrs.get("color")

        return attrs
