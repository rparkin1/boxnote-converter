"""Custom exceptions for Box Notes converter."""


class BoxNotesError(Exception):
    """Base exception for all Box Notes converter errors."""

    pass


class UnsupportedFormatError(BoxNotesError):
    """Raised when Box Notes format is not recognized or supported."""

    pass


class ParsingError(BoxNotesError):
    """Raised when parsing Box Notes JSON fails."""

    pass


class ConversionError(BoxNotesError):
    """Raised when converting document to output format fails."""

    pass


class ValidationError(BoxNotesError):
    """Raised when document structure validation fails."""

    pass
