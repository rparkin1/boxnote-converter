"""Tests for data models."""

import pytest

from boxnotes.models import (
    Block,
    BlockType,
    Document,
    ListType,
    TextAttributes,
    TextSpan,
)


class TestTextAttributes:
    """Tests for TextAttributes class."""

    def test_default_attributes(self) -> None:
        """Test default text attributes are all false/None."""
        attrs = TextAttributes()
        assert attrs.bold is False
        assert attrs.italic is False
        assert attrs.code is False
        assert attrs.link is None

    def test_is_empty_default(self) -> None:
        """Test is_empty returns True for default attributes."""
        attrs = TextAttributes()
        assert attrs.is_empty() is True

    def test_is_empty_with_bold(self) -> None:
        """Test is_empty returns False when bold is set."""
        attrs = TextAttributes(bold=True)
        assert attrs.is_empty() is False

    def test_is_empty_with_link(self) -> None:
        """Test is_empty returns False when link is set."""
        attrs = TextAttributes(link="https://example.com")
        assert attrs.is_empty() is False


class TestTextSpan:
    """Tests for TextSpan class."""

    def test_create_basic_text_span(self) -> None:
        """Test creating a basic text span."""
        span = TextSpan(text="Hello world")
        assert span.text == "Hello world"
        assert span.attributes.is_empty()

    def test_create_text_span_with_attributes(self) -> None:
        """Test creating text span with formatting."""
        attrs = TextAttributes(bold=True, italic=True)
        span = TextSpan(text="Bold and italic", attributes=attrs)
        assert span.text == "Bold and italic"
        assert span.attributes.bold is True
        assert span.attributes.italic is True

    def test_text_span_requires_string(self) -> None:
        """Test TextSpan raises TypeError for non-string text."""
        with pytest.raises(TypeError, match="must be a string"):
            TextSpan(text=123)  # type: ignore

    def test_text_span_requires_text_attributes(self) -> None:
        """Test TextSpan raises TypeError for invalid attributes."""
        with pytest.raises(TypeError, match="must be a TextAttributes"):
            TextSpan(text="Hello", attributes="not attributes")  # type: ignore


class TestBlock:
    """Tests for Block class."""

    def test_create_paragraph_block(self) -> None:
        """Test creating a paragraph block."""
        span = TextSpan(text="Hello")
        block = Block(type=BlockType.PARAGRAPH, content=[span])
        assert block.type == BlockType.PARAGRAPH
        assert len(block.content) == 1
        assert block.get_text() == "Hello"

    def test_create_heading_block(self) -> None:
        """Test creating a heading block."""
        span = TextSpan(text="Title")
        block = Block(type=BlockType.HEADING, content=[span], heading_level=1)
        assert block.type == BlockType.HEADING
        assert block.heading_level == 1

    def test_heading_requires_level(self) -> None:
        """Test heading block requires heading_level."""
        span = TextSpan(text="Title")
        with pytest.raises(ValueError, match="must have heading_level"):
            Block(type=BlockType.HEADING, content=[span])

    def test_heading_requires_valid_level(self) -> None:
        """Test heading block requires level 1, 2, or 3."""
        span = TextSpan(text="Title")
        with pytest.raises(ValueError, match="heading_level of 1, 2, or 3"):
            Block(type=BlockType.HEADING, content=[span], heading_level=4)

    def test_list_block_requires_list_type(self) -> None:
        """Test list block requires list_type."""
        with pytest.raises(ValueError, match="must have a list_type"):
            Block(type=BlockType.LIST)

    def test_create_list_block(self) -> None:
        """Test creating a list block."""
        block = Block(type=BlockType.LIST, list_type=ListType.BULLET)
        assert block.type == BlockType.LIST
        assert block.list_type == ListType.BULLET

    def test_block_with_children(self) -> None:
        """Test block with child blocks."""
        child1 = Block(type=BlockType.LIST_ITEM, content=[TextSpan(text="Item 1")])
        child2 = Block(type=BlockType.LIST_ITEM, content=[TextSpan(text="Item 2")])
        parent = Block(
            type=BlockType.LIST, list_type=ListType.BULLET, children=[child1, child2]
        )
        assert parent.has_children()
        assert len(parent.children) == 2

    def test_block_get_text(self) -> None:
        """Test getting text from block."""
        span1 = TextSpan(text="Hello ")
        span2 = TextSpan(text="world")
        block = Block(type=BlockType.PARAGRAPH, content=[span1, span2])
        assert block.get_text() == "Hello world"


class TestDocument:
    """Tests for Document class."""

    def test_create_empty_document(self) -> None:
        """Test creating an empty document."""
        doc = Document()
        assert len(doc.blocks) == 0
        assert doc.block_count() == 0

    def test_create_document_with_blocks(self) -> None:
        """Test creating document with blocks."""
        block1 = Block(type=BlockType.PARAGRAPH, content=[TextSpan(text="Para 1")])
        block2 = Block(type=BlockType.PARAGRAPH, content=[TextSpan(text="Para 2")])
        doc = Document(blocks=[block1, block2])
        assert len(doc.blocks) == 2
        assert doc.block_count() == 2

    def test_document_get_text(self) -> None:
        """Test getting all text from document."""
        block1 = Block(type=BlockType.PARAGRAPH, content=[TextSpan(text="Paragraph 1")])
        block2 = Block(type=BlockType.PARAGRAPH, content=[TextSpan(text="Paragraph 2")])
        doc = Document(blocks=[block1, block2])
        text = doc.get_text()
        assert "Paragraph 1" in text
        assert "Paragraph 2" in text

    def test_document_block_count_with_children(self) -> None:
        """Test block count includes children."""
        item1 = Block(type=BlockType.LIST_ITEM, content=[TextSpan(text="Item 1")])
        item2 = Block(type=BlockType.LIST_ITEM, content=[TextSpan(text="Item 2")])
        list_block = Block(
            type=BlockType.LIST, list_type=ListType.BULLET, children=[item1, item2]
        )
        doc = Document(blocks=[list_block])
        assert doc.block_count() == 3  # 1 list + 2 items

    def test_document_requires_block_instances(self) -> None:
        """Test document validates block types."""
        with pytest.raises(TypeError, match="must be Block instances"):
            Document(blocks=["not a block"])  # type: ignore
