"""Tests for format detection."""

import pytest

from boxnotes.detector import detect_format, validate_new_format, validate_old_format
from boxnotes.exceptions import UnsupportedFormatError
from boxnotes.models import FormatType


class TestDetectFormat:
    """Tests for detect_format function."""

    def test_detect_old_format_basic(self) -> None:
        """Test detection of old format with minimal structure."""
        data = {"atext": {"text": "Hello world", "attribs": "*0+b"}}
        assert detect_format(data) == FormatType.OLD

    def test_detect_old_format_with_pool(self) -> None:
        """Test detection of old format with pool."""
        data = {
            "atext": {
                "text": "Hello world",
                "attribs": "*0+b",
                "pool": {"numToAttrib": {"0": ["bold", "true"]}},
            }
        }
        assert detect_format(data) == FormatType.OLD

    def test_detect_new_format_basic(self) -> None:
        """Test detection of new format with doc wrapper."""
        data = {"doc": {"type": "doc", "content": []}}
        assert detect_format(data) == FormatType.NEW

    def test_detect_new_format_direct(self) -> None:
        """Test detection of new format without doc wrapper."""
        data = {"type": "doc", "content": []}
        assert detect_format(data) == FormatType.NEW

    def test_detect_new_format_with_content(self) -> None:
        """Test detection of new format with actual content."""
        data = {
            "doc": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Hello"}],
                    }
                ],
            }
        }
        assert detect_format(data) == FormatType.NEW

    def test_detect_format_empty_dict(self) -> None:
        """Test detection fails with empty dictionary."""
        with pytest.raises(UnsupportedFormatError, match="Unknown Box Notes format"):
            detect_format({})

    def test_detect_format_not_dict(self) -> None:
        """Test detection fails when data is not a dictionary."""
        with pytest.raises(UnsupportedFormatError, match="must be a dictionary"):
            detect_format("not a dict")  # type: ignore

    def test_detect_format_invalid_atext(self) -> None:
        """Test detection fails with invalid atext structure."""
        data = {"atext": "not a dict"}
        with pytest.raises(UnsupportedFormatError, match="must be a dictionary"):
            detect_format(data)

    def test_detect_format_missing_required_keys(self) -> None:
        """Test detection fails when required keys are missing."""
        data = {"atext": {"text": "Hello"}}  # Missing 'attribs'
        with pytest.raises(UnsupportedFormatError, match="missing required keys"):
            detect_format(data)

    def test_detect_format_invalid_doc(self) -> None:
        """Test detection fails with invalid doc structure."""
        data = {"doc": "not a dict"}
        with pytest.raises(UnsupportedFormatError, match="must be a dictionary"):
            detect_format(data)

    def test_detect_format_wrong_doc_type(self) -> None:
        """Test detection fails when doc.type is not 'doc'."""
        data = {"doc": {"type": "paragraph", "content": []}}
        with pytest.raises(UnsupportedFormatError, match="must be 'doc'"):
            detect_format(data)

    def test_detect_format_missing_content(self) -> None:
        """Test detection fails when doc is missing content."""
        data = {"doc": {"type": "doc"}}  # Missing 'content'
        with pytest.raises(UnsupportedFormatError, match="missing 'content'"):
            detect_format(data)


class TestValidateOldFormat:
    """Tests for validate_old_format function."""

    def test_validate_valid_old_format(self) -> None:
        """Test validation passes for valid old format."""
        data = {"atext": {"text": "Hello", "attribs": "*0+5"}}
        assert validate_old_format(data) is True

    def test_validate_old_format_with_pool(self) -> None:
        """Test validation passes with pool."""
        data = {
            "atext": {
                "text": "Hello",
                "attribs": "*0+5",
                "pool": {"numToAttrib": {}},
            }
        }
        assert validate_old_format(data) is True

    def test_validate_old_format_missing_atext(self) -> None:
        """Test validation fails when atext is missing."""
        with pytest.raises(UnsupportedFormatError, match="missing 'atext'"):
            validate_old_format({})

    def test_validate_old_format_invalid_atext_type(self) -> None:
        """Test validation fails when atext is not a dict."""
        with pytest.raises(UnsupportedFormatError, match="must be a dictionary"):
            validate_old_format({"atext": "not a dict"})

    def test_validate_old_format_missing_text(self) -> None:
        """Test validation fails when text is missing."""
        with pytest.raises(UnsupportedFormatError, match="must be a string"):
            validate_old_format({"atext": {"attribs": "*0+5"}})

    def test_validate_old_format_missing_attribs(self) -> None:
        """Test validation fails when attribs is missing."""
        with pytest.raises(UnsupportedFormatError, match="must be a string"):
            validate_old_format({"atext": {"text": "Hello"}})

    def test_validate_old_format_invalid_pool_type(self) -> None:
        """Test validation fails when pool is not a dict."""
        with pytest.raises(UnsupportedFormatError, match="must be a dictionary"):
            validate_old_format(
                {"atext": {"text": "Hello", "attribs": "*0+5", "pool": "not a dict"}}
            )


class TestValidateNewFormat:
    """Tests for validate_new_format function."""

    def test_validate_valid_new_format(self) -> None:
        """Test validation passes for valid new format."""
        data = {"doc": {"type": "doc", "content": []}}
        assert validate_new_format(data) is True

    def test_validate_new_format_direct(self) -> None:
        """Test validation passes for direct doc format."""
        data = {"type": "doc", "content": []}
        assert validate_new_format(data) is True

    def test_validate_new_format_wrong_type(self) -> None:
        """Test validation fails with wrong type."""
        data = {"doc": {"type": "paragraph", "content": []}}
        with pytest.raises(UnsupportedFormatError, match="must be 'doc'"):
            validate_new_format(data)

    def test_validate_new_format_missing_content(self) -> None:
        """Test validation fails when content is missing."""
        data = {"doc": {"type": "doc"}}
        with pytest.raises(UnsupportedFormatError, match="missing 'content'"):
            validate_new_format(data)

    def test_validate_new_format_invalid_content_type(self) -> None:
        """Test validation fails when content is not a list."""
        data = {"doc": {"type": "doc", "content": "not a list"}}
        with pytest.raises(UnsupportedFormatError, match="must be a list"):
            validate_new_format(data)
