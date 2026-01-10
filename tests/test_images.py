"""Tests for image extraction and handling utilities."""

import base64
from pathlib import Path

import pytest

from boxnotes.models import Block, BlockType, Document
from boxnotes.utils.images import (
    extract_image,
    generate_image_filename,
    get_file_extension,
    is_data_uri,
    parse_data_uri,
    sanitize_image_url,
)


class TestDataUriDetection:
    """Tests for data URI detection."""

    def test_is_data_uri_with_data_uri(self) -> None:
        """Test detecting data URI."""
        assert is_data_uri("data:image/png;base64,iVBORw0KGgo=")

    def test_is_data_uri_with_http_url(self) -> None:
        """Test detecting HTTP URL (not data URI)."""
        assert not is_data_uri("https://example.com/image.png")

    def test_is_data_uri_with_relative_path(self) -> None:
        """Test detecting relative path (not data URI)."""
        assert not is_data_uri("images/photo.jpg")


class TestParseDataUri:
    """Tests for data URI parsing."""

    def test_parse_simple_data_uri(self) -> None:
        """Test parsing simple data URI."""
        # 1x1 transparent PNG
        data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        mime_type, data = parse_data_uri(data_uri)

        assert mime_type == "image/png"
        assert data is not None
        assert len(data) > 0

    def test_parse_data_uri_without_mime(self) -> None:
        """Test parsing data URI without MIME type."""
        data_uri = "data:;base64,SGVsbG8="
        mime_type, data = parse_data_uri(data_uri)

        assert mime_type == "application/octet-stream"
        assert data == b"Hello"

    def test_parse_invalid_data_uri(self) -> None:
        """Test parsing invalid data URI."""
        mime_type, data = parse_data_uri("not a data uri")

        assert mime_type is None
        assert data is None

    def test_parse_http_url(self) -> None:
        """Test parsing HTTP URL (should fail)."""
        mime_type, data = parse_data_uri("https://example.com/image.png")

        assert mime_type is None
        assert data is None


class TestFileExtension:
    """Tests for file extension extraction."""

    def test_get_png_extension(self) -> None:
        """Test getting .png extension."""
        assert get_file_extension("image/png") == ".png"

    def test_get_jpeg_extension(self) -> None:
        """Test getting .jpg extension."""
        assert get_file_extension("image/jpeg") == ".jpg"

    def test_get_gif_extension(self) -> None:
        """Test getting .gif extension."""
        assert get_file_extension("image/gif") == ".gif"

    def test_get_unknown_extension(self) -> None:
        """Test getting default extension for unknown MIME type."""
        assert get_file_extension("image/unknown") == ".png"


class TestGenerateImageFilename:
    """Tests for image filename generation."""

    def test_generate_filename_with_data(self) -> None:
        """Test generating filename from image data."""
        data = b"test image data"
        filename = generate_image_filename(data, "image/png")

        assert filename.startswith("image_")
        assert filename.endswith(".png")
        assert len(filename) > 10  # Has hash

    def test_generate_filename_consistent(self) -> None:
        """Test that same data generates same filename."""
        data = b"test image data"
        filename1 = generate_image_filename(data, "image/png")
        filename2 = generate_image_filename(data, "image/png")

        assert filename1 == filename2

    def test_generate_filename_different_data(self) -> None:
        """Test that different data generates different filename."""
        data1 = b"test image data 1"
        data2 = b"test image data 2"
        filename1 = generate_image_filename(data1, "image/png")
        filename2 = generate_image_filename(data2, "image/png")

        assert filename1 != filename2


class TestExtractImage:
    """Tests for image extraction."""

    def test_extract_data_uri_image(self, tmp_path: Path) -> None:
        """Test extracting image from data URI."""
        # 1x1 transparent PNG
        data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        result = extract_image(data_uri, tmp_path)

        assert result is not None
        assert result.endswith(".png")
        assert (tmp_path / result).exists()

    def test_extract_http_url(self, tmp_path: Path) -> None:
        """Test extracting external HTTP URL (returns URL as-is)."""
        url = "https://example.com/image.png"

        result = extract_image(url, tmp_path)

        assert result == url

    def test_extract_empty_url(self, tmp_path: Path) -> None:
        """Test extracting with empty URL."""
        result = extract_image("", tmp_path)

        assert result is None


class TestSanitizeImageUrl:
    """Tests for URL sanitization."""

    def test_sanitize_normal_url(self) -> None:
        """Test sanitizing normal HTTP URL."""
        url = "https://example.com/image.png"
        assert sanitize_image_url(url) == url

    def test_sanitize_data_uri(self) -> None:
        """Test sanitizing valid data URI."""
        url = "data:image/png;base64,iVBORw0KGgo="
        assert sanitize_image_url(url) == url

    def test_sanitize_javascript_url(self) -> None:
        """Test sanitizing dangerous JavaScript URL."""
        url = "javascript:alert(1)"
        assert sanitize_image_url(url) == ""

    def test_sanitize_html_data_uri(self) -> None:
        """Test sanitizing HTML data URI (dangerous)."""
        url = "data:text/html,<script>alert(1)</script>"
        assert sanitize_image_url(url) == ""

    def test_sanitize_empty_url(self) -> None:
        """Test sanitizing empty URL."""
        assert sanitize_image_url("") == ""


class TestImageBlockConversion:
    """Tests for converting image blocks."""

    def test_create_image_block(self) -> None:
        """Test creating image block."""
        block = Block(
            type=BlockType.IMAGE,
            image_url="https://example.com/image.png",
            image_alt="Test image",
            image_title="A test image",
        )

        assert block.type == BlockType.IMAGE
        assert block.image_url == "https://example.com/image.png"
        assert block.image_alt == "Test image"
        assert block.image_title == "A test image"

    def test_markdown_conversion_with_image(self) -> None:
        """Test converting document with image to markdown."""
        from boxnotes.converters.markdown import MarkdownConverter

        block = Block(
            type=BlockType.IMAGE,
            image_url="https://example.com/image.png",
            image_alt="Test image",
        )
        document = Document(blocks=[block])

        converter = MarkdownConverter()
        result = converter.convert(document)

        assert "![Test image](https://example.com/image.png)" in result

    def test_markdown_conversion_with_image_title(self) -> None:
        """Test converting image with title to markdown."""
        from boxnotes.converters.markdown import MarkdownConverter

        block = Block(
            type=BlockType.IMAGE,
            image_url="https://example.com/image.png",
            image_alt="Test image",
            image_title="My Image",
        )
        document = Document(blocks=[block])

        converter = MarkdownConverter()
        result = converter.convert(document)

        assert '![Test image](https://example.com/image.png "My Image")' in result

    def test_plaintext_conversion_with_image(self) -> None:
        """Test converting document with image to plain text."""
        from boxnotes.converters.plaintext import PlainTextConverter

        block = Block(
            type=BlockType.IMAGE,
            image_url="https://example.com/image.png",
            image_alt="Test image",
        )
        document = Document(blocks=[block])

        converter = PlainTextConverter()
        result = converter.convert(document)

        assert "[Image: Test image] (https://example.com/image.png)" in result
