"""Base class for document converters."""

from abc import ABC, abstractmethod

from boxnotes.models import Document


class DocumentConverter(ABC):
    """Abstract base class for document converters."""

    @abstractmethod
    def convert(self, document: Document) -> str:
        """
        Convert a Document to output format.

        Args:
            document: Document to convert

        Returns:
            String representation in target format

        Raises:
            ConversionError: If conversion fails
        """
        pass

    def convert_file(self, input_path: str, output_path: str) -> None:
        """
        Convert a Box Notes file and write output.

        Args:
            input_path: Path to input .boxnote file
            output_path: Path to write output file

        Raises:
            FileNotFoundError: If input file doesn't exist
            ConversionError: If conversion fails
            IOError: If writing output fails
        """
        from pathlib import Path

        from boxnotes.detector import detect_format
        from boxnotes.models import FormatType

        # This is a convenience method that would need parser selection
        # Actual implementation will be in CLI
        raise NotImplementedError(
            "Use CLI or manually parse with appropriate parser first"
        )
