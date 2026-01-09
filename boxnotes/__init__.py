"""Box Notes converter - Convert Box Notes to Markdown and plain text."""

__version__ = "0.1.0"

from boxnotes.exceptions import (
    BoxNotesError,
    ConversionError,
    ParsingError,
    UnsupportedFormatError,
    ValidationError,
)
from boxnotes.models import (
    Block,
    BlockType,
    Document,
    FormatType,
    ListType,
    TextAttributes,
    TextSpan,
)

__all__ = [
    "BoxNotesError",
    "ConversionError",
    "ParsingError",
    "UnsupportedFormatError",
    "ValidationError",
    "Block",
    "BlockType",
    "Document",
    "FormatType",
    "ListType",
    "TextAttributes",
    "TextSpan",
    "__version__",
]
