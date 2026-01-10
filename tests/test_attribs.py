"""Tests for attribute decompression utilities."""

import pytest

from boxnotes.utils.attribs import (
    AttributeChunk,
    decode_base36,
    detect_block_type,
    extract_text_spans,
    parse_attribute_string,
    resolve_attributes,
)


class TestDecodeBase36:
    """Tests for base-36 decoding."""

    def test_decode_digit(self) -> None:
        """Test decoding single digits."""
        assert decode_base36("0") == 0
        assert decode_base36("5") == 5
        assert decode_base36("9") == 9

    def test_decode_letter(self) -> None:
        """Test decoding single letters."""
        assert decode_base36("a") == 10
        assert decode_base36("A") == 10  # Case insensitive
        assert decode_base36("z") == 35
        assert decode_base36("Z") == 35

    def test_decode_multi_char(self) -> None:
        """Test decoding multi-character strings."""
        assert decode_base36("10") == 36  # 1*36 + 0
        assert decode_base36("b") == 11
        assert decode_base36("1b") == 47  # 1*36 + 11

    def test_decode_invalid(self) -> None:
        """Test decoding invalid strings raises ValueError."""
        with pytest.raises(ValueError, match="Invalid base-36"):
            decode_base36("invalid!")


class TestAttributeChunk:
    """Tests for AttributeChunk dataclass."""

    def test_create_basic_chunk(self) -> None:
        """Test creating a basic attribute chunk."""
        chunk = AttributeChunk(attributes={0}, num_characters=5)
        assert chunk.attributes == {0}
        assert chunk.num_characters == 5
        assert chunk.num_linebreaks == 0

    def test_create_chunk_with_linebreaks(self) -> None:
        """Test creating chunk with line breaks."""
        chunk = AttributeChunk(attributes={0, 1}, num_characters=10, num_linebreaks=2)
        assert chunk.attributes == {0, 1}
        assert chunk.num_characters == 10
        assert chunk.num_linebreaks == 2

    def test_chunk_validates_negative_chars(self) -> None:
        """Test chunk raises ValueError for negative characters."""
        with pytest.raises(ValueError, match="must be non-negative"):
            AttributeChunk(attributes={0}, num_characters=-1)

    def test_chunk_validates_negative_breaks(self) -> None:
        """Test chunk raises ValueError for negative line breaks."""
        with pytest.raises(ValueError, match="must be non-negative"):
            AttributeChunk(attributes={0}, num_characters=5, num_linebreaks=-1)


class TestParseAttributeString:
    """Tests for attribute string parsing."""

    def test_parse_simple_string(self) -> None:
        """Test parsing simple attribute string."""
        chunks = parse_attribute_string("*0+5")
        assert len(chunks) == 1
        assert chunks[0].attributes == {0}
        assert chunks[0].num_characters == 5
        assert chunks[0].num_linebreaks == 0

    def test_parse_multiple_attributes(self) -> None:
        """Test parsing string with multiple attributes."""
        chunks = parse_attribute_string("*0*1+a")
        assert len(chunks) == 1
        assert chunks[0].attributes == {0, 1}
        assert chunks[0].num_characters == 10  # 'a' in base-36 is 10

    def test_parse_with_linebreaks(self) -> None:
        """Test parsing string with line breaks."""
        chunks = parse_attribute_string("*0+5|1")
        assert len(chunks) == 1
        assert chunks[0].attributes == {0}
        assert chunks[0].num_characters == 5
        assert chunks[0].num_linebreaks == 1

    def test_parse_multiple_chunks(self) -> None:
        """Test parsing multiple chunks."""
        chunks = parse_attribute_string("*0+5|1+2")
        assert len(chunks) == 2
        # First chunk: 5 chars with attr 0, 1 linebreak
        assert chunks[0].attributes == {0}
        assert chunks[0].num_characters == 5
        assert chunks[0].num_linebreaks == 1
        # Second chunk: 2 chars, no attributes
        assert chunks[1].attributes == set()
        assert chunks[1].num_characters == 2
        assert chunks[1].num_linebreaks == 0

    def test_parse_complex_string(self) -> None:
        """Test parsing complex attribute string."""
        chunks = parse_attribute_string("*0*1+c|1+1*2+5")
        assert len(chunks) == 3
        # First chunk
        assert chunks[0].attributes == {0, 1}
        assert chunks[0].num_characters == 12  # 'c' in base-36
        assert chunks[0].num_linebreaks == 1
        # Second chunk
        assert chunks[1].attributes == set()
        assert chunks[1].num_characters == 1
        # Third chunk
        assert chunks[2].attributes == {2}
        assert chunks[2].num_characters == 5

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string."""
        chunks = parse_attribute_string("")
        assert chunks == []

    def test_parse_no_attributes(self) -> None:
        """Test parsing string with no attributes."""
        chunks = parse_attribute_string("+5")
        assert len(chunks) == 1
        assert chunks[0].attributes == set()
        assert chunks[0].num_characters == 5


class TestResolveAttributes:
    """Tests for attribute resolution."""

    def test_resolve_single_attribute(self) -> None:
        """Test resolving single attribute."""
        pool = {"numToAttrib": {"0": ["bold", "true"]}}
        attrs = resolve_attributes({0}, pool)
        assert attrs == [("bold", "true")]

    def test_resolve_multiple_attributes(self) -> None:
        """Test resolving multiple attributes."""
        pool = {"numToAttrib": {"0": ["bold", "true"], "1": ["italic", "true"]}}
        attrs = resolve_attributes({0, 1}, pool)
        assert len(attrs) == 2
        assert ("bold", "true") in attrs
        assert ("italic", "true") in attrs

    def test_resolve_missing_index(self) -> None:
        """Test resolving with missing pool index."""
        pool = {"numToAttrib": {"0": ["bold", "true"]}}
        attrs = resolve_attributes({0, 99}, pool)  # 99 doesn't exist
        assert attrs == [("bold", "true")]

    def test_resolve_empty_pool(self) -> None:
        """Test resolving with empty pool."""
        attrs = resolve_attributes({0, 1}, {})
        assert attrs == []

    def test_resolve_no_numToAttrib(self) -> None:
        """Test resolving when pool has no numToAttrib."""
        attrs = resolve_attributes({0}, {"other": "data"})
        assert attrs == []

    def test_resolve_sorted_order(self) -> None:
        """Test attributes are resolved in sorted order by index."""
        pool = {
            "numToAttrib": {
                "0": ["attr0", "val0"],
                "5": ["attr5", "val5"],
                "2": ["attr2", "val2"],
            }
        }
        attrs = resolve_attributes({5, 0, 2}, pool)
        # Should be sorted: 0, 2, 5
        assert attrs == [("attr0", "val0"), ("attr2", "val2"), ("attr5", "val5")]


class TestExtractTextSpans:
    """Tests for text span extraction."""

    def test_extract_single_span(self) -> None:
        """Test extracting single text span."""
        text = "Hello"
        chunks = [AttributeChunk({0}, 5, 0)]
        pool = {"numToAttrib": {"0": ["bold", "true"]}}
        spans = extract_text_spans(text, chunks, pool)
        assert len(spans) == 1
        assert spans[0] == ("Hello", [("bold", "true")])

    def test_extract_multiple_spans(self) -> None:
        """Test extracting multiple text spans."""
        text = "Hello world"
        chunks = [
            AttributeChunk({0}, 5, 0),  # "Hello"
            AttributeChunk({1}, 6, 0),  # " world"
        ]
        pool = {"numToAttrib": {"0": ["bold", "true"], "1": ["italic", "true"]}}
        spans = extract_text_spans(text, chunks, pool)
        assert len(spans) == 2
        assert spans[0] == ("Hello", [("bold", "true")])
        assert spans[1] == (" world", [("italic", "true")])

    def test_extract_with_linebreaks(self) -> None:
        """Test extracting spans with line breaks."""
        text = "Hello\nworld"
        chunks = [
            AttributeChunk({0}, 5, 1),  # "Hello" + 1 linebreak
            AttributeChunk({1}, 5, 0),  # "world"
        ]
        pool = {"numToAttrib": {"0": ["bold", "true"], "1": ["italic", "true"]}}
        spans = extract_text_spans(text, chunks, pool)
        assert len(spans) == 3
        assert spans[0] == ("Hello", [("bold", "true")])
        assert spans[1] == ("\n", [])
        assert spans[2] == ("world", [("italic", "true")])

    def test_extract_empty_chunks(self) -> None:
        """Test extracting with empty chunk list."""
        spans = extract_text_spans("Hello", [], {})
        assert spans == []

    def test_extract_span_no_attributes(self) -> None:
        """Test extracting span with no attributes."""
        text = "Plain text"
        chunks = [AttributeChunk(set(), 10, 0)]
        spans = extract_text_spans(text, chunks, {})
        assert len(spans) == 1
        assert spans[0] == ("Plain text", [])


class TestDetectBlockType:
    """Tests for block type detection."""

    def test_detect_heading(self) -> None:
        """Test detecting heading block."""
        attrs = [("heading", "h1")]
        assert detect_block_type(attrs) == "heading"

    def test_detect_list(self) -> None:
        """Test detecting list block."""
        attrs = [("list", "number1")]
        assert detect_block_type(attrs) == "list"

    def test_detect_code_block(self) -> None:
        """Test detecting code block."""
        attrs = [("code", "true")]
        assert detect_block_type(attrs) == "code_block"

    def test_detect_blockquote(self) -> None:
        """Test detecting blockquote."""
        attrs = [("blockquote", "true")]
        assert detect_block_type(attrs) == "blockquote"

    def test_detect_paragraph_default(self) -> None:
        """Test detecting paragraph as default."""
        attrs = [("bold", "true"), ("italic", "true")]
        assert detect_block_type(attrs) == "paragraph"

    def test_detect_empty_attributes(self) -> None:
        """Test detecting with empty attributes."""
        assert detect_block_type([]) == "paragraph"
