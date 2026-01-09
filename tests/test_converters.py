"""Tests for document converters."""

from boxnotes.converters.markdown import MarkdownConverter
from boxnotes.converters.plaintext import PlainTextConverter
from boxnotes.models import (
    Block,
    BlockType,
    Document,
    ListType,
    TextAttributes,
    TextSpan,
)


class TestMarkdownConverter:
    """Tests for Markdown converter."""

    def test_convert_empty_document(self):
        """Test converting empty document."""
        converter = MarkdownConverter()
        document = Document(blocks=[])
        result = converter.convert(document)
        assert result == ""

    def test_convert_simple_paragraph(self):
        """Test converting simple paragraph."""
        converter = MarkdownConverter()
        block = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="Hello world", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "Hello world"

    def test_convert_paragraph_with_bold(self):
        """Test converting paragraph with bold text."""
        converter = MarkdownConverter()
        attrs = TextAttributes(bold=True)
        block = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="Bold text", attributes=attrs)],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "**Bold text**"

    def test_convert_paragraph_with_italic(self):
        """Test converting paragraph with italic text."""
        converter = MarkdownConverter()
        attrs = TextAttributes(italic=True)
        block = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="Italic text", attributes=attrs)],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "*Italic text*"

    def test_convert_paragraph_with_bold_italic(self):
        """Test converting paragraph with bold and italic text."""
        converter = MarkdownConverter()
        attrs = TextAttributes(bold=True, italic=True)
        block = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="Bold italic", attributes=attrs)],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "***Bold italic***"

    def test_convert_paragraph_with_code(self):
        """Test converting paragraph with inline code."""
        converter = MarkdownConverter()
        attrs = TextAttributes(code=True)
        block = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="code", attributes=attrs)],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "`code`"

    def test_convert_paragraph_with_strike(self):
        """Test converting paragraph with strikethrough text."""
        converter = MarkdownConverter()
        attrs = TextAttributes(strike=True)
        block = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="strike", attributes=attrs)],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "~~strike~~"

    def test_convert_paragraph_with_link(self):
        """Test converting paragraph with link."""
        converter = MarkdownConverter()
        attrs = TextAttributes(link="https://example.com")
        block = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="link", attributes=attrs)],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "[link](https://example.com)"

    def test_convert_heading_level1(self):
        """Test converting heading level 1."""
        converter = MarkdownConverter()
        block = Block(
            type=BlockType.HEADING,
            heading_level=1,
            content=[TextSpan(text="Heading 1", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "# Heading 1"

    def test_convert_heading_level2(self):
        """Test converting heading level 2."""
        converter = MarkdownConverter()
        block = Block(
            type=BlockType.HEADING,
            heading_level=2,
            content=[TextSpan(text="Heading 2", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "## Heading 2"

    def test_convert_heading_level3(self):
        """Test converting heading level 3."""
        converter = MarkdownConverter()
        block = Block(
            type=BlockType.HEADING,
            heading_level=3,
            content=[TextSpan(text="Heading 3", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "### Heading 3"

    def test_convert_code_block(self):
        """Test converting code block."""
        converter = MarkdownConverter()
        block = Block(
            type=BlockType.CODE_BLOCK,
            content=[TextSpan(text="def hello():\n    print('hello')", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert "```" in result
        assert "def hello():" in result

    def test_convert_blockquote(self):
        """Test converting blockquote."""
        converter = MarkdownConverter()
        block = Block(
            type=BlockType.BLOCKQUOTE,
            content=[TextSpan(text="Quote text", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "> Quote text"

    def test_convert_horizontal_rule(self):
        """Test converting horizontal rule."""
        converter = MarkdownConverter()
        block = Block(type=BlockType.HORIZONTAL_RULE, content=[])
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "---"

    def test_convert_bullet_list(self):
        """Test converting bullet list."""
        converter = MarkdownConverter()
        item1 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="Item 1", attributes=TextAttributes())],
        )
        item2 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="Item 2", attributes=TextAttributes())],
        )
        list_block = Block(
            type=BlockType.LIST,
            list_type=ListType.BULLET,
            children=[item1, item2],
        )
        document = Document(blocks=[list_block])
        result = converter.convert(document)
        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_convert_ordered_list(self):
        """Test converting ordered list."""
        converter = MarkdownConverter()
        item1 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="First", attributes=TextAttributes())],
        )
        item2 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="Second", attributes=TextAttributes())],
        )
        list_block = Block(
            type=BlockType.LIST,
            list_type=ListType.ORDERED,
            children=[item1, item2],
        )
        document = Document(blocks=[list_block])
        result = converter.convert(document)
        assert "1. First" in result
        assert "2. Second" in result

    def test_convert_check_list(self):
        """Test converting check list."""
        converter = MarkdownConverter()
        item1 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="Done", attributes=TextAttributes())],
            checked=True,
        )
        item2 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="Todo", attributes=TextAttributes())],
            checked=False,
        )
        list_block = Block(
            type=BlockType.LIST,
            list_type=ListType.CHECK,
            children=[item1, item2],
        )
        document = Document(blocks=[list_block])
        result = converter.convert(document)
        assert "- [x] Done" in result
        assert "- [ ] Todo" in result

    def test_convert_table(self):
        """Test converting table."""
        converter = MarkdownConverter()
        cell1 = Block(
            type=BlockType.TABLE_CELL,
            content=[TextSpan(text="A1", attributes=TextAttributes())],
        )
        cell2 = Block(
            type=BlockType.TABLE_CELL,
            content=[TextSpan(text="B1", attributes=TextAttributes())],
        )
        row1 = Block(
            type=BlockType.TABLE_ROW,
            children=[cell1, cell2],
        )
        cell3 = Block(
            type=BlockType.TABLE_CELL,
            content=[TextSpan(text="A2", attributes=TextAttributes())],
        )
        cell4 = Block(
            type=BlockType.TABLE_CELL,
            content=[TextSpan(text="B2", attributes=TextAttributes())],
        )
        row2 = Block(
            type=BlockType.TABLE_ROW,
            children=[cell3, cell4],
        )
        table = Block(
            type=BlockType.TABLE,
            children=[row1, row2],
        )
        document = Document(blocks=[table])
        result = converter.convert(document)
        assert "| A1 | B1 |" in result
        assert "| --- | --- |" in result
        assert "| A2 | B2 |" in result

    def test_convert_multiple_blocks(self):
        """Test converting document with multiple blocks."""
        converter = MarkdownConverter()
        heading = Block(
            type=BlockType.HEADING,
            heading_level=1,
            content=[TextSpan(text="Title", attributes=TextAttributes())],
        )
        para = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="Content", attributes=TextAttributes())],
        )
        document = Document(blocks=[heading, para])
        result = converter.convert(document)
        assert "# Title" in result
        assert "Content" in result
        assert result.count("\n\n") >= 1  # Blocks separated by double newline


class TestPlainTextConverter:
    """Tests for plain text converter."""

    def test_convert_empty_document(self):
        """Test converting empty document."""
        converter = PlainTextConverter()
        document = Document(blocks=[])
        result = converter.convert(document)
        assert result == ""

    def test_convert_simple_paragraph(self):
        """Test converting simple paragraph."""
        converter = PlainTextConverter()
        block = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="Hello world", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "Hello world"

    def test_convert_paragraph_strips_formatting(self):
        """Test converting paragraph strips formatting."""
        converter = PlainTextConverter()
        attrs = TextAttributes(bold=True, italic=True, code=True)
        block = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="Formatted text", attributes=attrs)],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        # Plain text should not have markdown syntax
        assert result == "Formatted text"
        assert "**" not in result
        assert "*" not in result
        assert "`" not in result

    def test_convert_paragraph_with_link(self):
        """Test converting paragraph with link shows URL."""
        converter = PlainTextConverter()
        attrs = TextAttributes(link="https://example.com")
        block = Block(
            type=BlockType.PARAGRAPH,
            content=[TextSpan(text="link", attributes=attrs)],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert result == "link (https://example.com)"

    def test_convert_heading_level1(self):
        """Test converting heading level 1 with underline."""
        converter = PlainTextConverter()
        block = Block(
            type=BlockType.HEADING,
            heading_level=1,
            content=[TextSpan(text="Title", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert "Title" in result
        assert "=====" in result  # Level 1 uses =

    def test_convert_heading_level2(self):
        """Test converting heading level 2 with underline."""
        converter = PlainTextConverter()
        block = Block(
            type=BlockType.HEADING,
            heading_level=2,
            content=[TextSpan(text="Subtitle", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert "Subtitle" in result
        assert "--------" in result  # Level 2 uses -

    def test_convert_heading_level3(self):
        """Test converting heading level 3 with underline."""
        converter = PlainTextConverter()
        block = Block(
            type=BlockType.HEADING,
            heading_level=3,
            content=[TextSpan(text="Section", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert "Section" in result
        assert "~~~~~~~" in result  # Level 3 uses ~

    def test_convert_code_block(self):
        """Test converting code block with indentation."""
        converter = PlainTextConverter()
        block = Block(
            type=BlockType.CODE_BLOCK,
            content=[TextSpan(text="code here", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert "    code here" in result  # 4-space indent

    def test_convert_blockquote(self):
        """Test converting blockquote with prefix."""
        converter = PlainTextConverter()
        block = Block(
            type=BlockType.BLOCKQUOTE,
            content=[TextSpan(text="Quote", attributes=TextAttributes())],
        )
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert "    > Quote" in result

    def test_convert_horizontal_rule(self):
        """Test converting horizontal rule."""
        converter = PlainTextConverter()
        block = Block(type=BlockType.HORIZONTAL_RULE, content=[])
        document = Document(blocks=[block])
        result = converter.convert(document)
        assert "-" * 60 in result

    def test_convert_bullet_list(self):
        """Test converting bullet list with bullet character."""
        converter = PlainTextConverter()
        item1 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="Item 1", attributes=TextAttributes())],
        )
        list_block = Block(
            type=BlockType.LIST,
            list_type=ListType.BULLET,
            children=[item1],
        )
        document = Document(blocks=[list_block])
        result = converter.convert(document)
        assert "• Item 1" in result

    def test_convert_ordered_list(self):
        """Test converting ordered list with numbers."""
        converter = PlainTextConverter()
        item1 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="First", attributes=TextAttributes())],
        )
        item2 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="Second", attributes=TextAttributes())],
        )
        list_block = Block(
            type=BlockType.LIST,
            list_type=ListType.ORDERED,
            children=[item1, item2],
        )
        document = Document(blocks=[list_block])
        result = converter.convert(document)
        assert "1. First" in result
        assert "2. Second" in result

    def test_convert_check_list(self):
        """Test converting check list with check symbols."""
        converter = PlainTextConverter()
        item1 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="Done", attributes=TextAttributes())],
            checked=True,
        )
        item2 = Block(
            type=BlockType.LIST_ITEM,
            content=[TextSpan(text="Todo", attributes=TextAttributes())],
            checked=False,
        )
        list_block = Block(
            type=BlockType.LIST,
            list_type=ListType.CHECK,
            children=[item1, item2],
        )
        document = Document(blocks=[list_block])
        result = converter.convert(document)
        assert "☑ Done" in result
        assert "☐ Todo" in result

    def test_convert_table(self):
        """Test converting table with tab separation."""
        converter = PlainTextConverter()
        cell1 = Block(
            type=BlockType.TABLE_CELL,
            content=[TextSpan(text="A1", attributes=TextAttributes())],
        )
        cell2 = Block(
            type=BlockType.TABLE_CELL,
            content=[TextSpan(text="B1", attributes=TextAttributes())],
        )
        row = Block(
            type=BlockType.TABLE_ROW,
            children=[cell1, cell2],
        )
        table = Block(
            type=BlockType.TABLE,
            children=[row],
        )
        document = Document(blocks=[table])
        result = converter.convert(document)
        assert "A1\tB1" in result  # Tab-separated
