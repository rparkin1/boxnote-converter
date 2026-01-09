"""Base class for Box Notes parsers."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from boxnotes.models import Document


class BoxNoteParser(ABC):
    """Abstract base class for Box Notes parsers."""

    @abstractmethod
    def parse(self, data: Dict[str, Any]) -> Document:
        """
        Parse Box Notes JSON data into a Document.

        Args:
            data: Parsed JSON data from Box Notes file

        Returns:
            Document object with parsed content

        Raises:
            ParsingError: If parsing fails
        """
        pass

    def parse_file(self, file_path: str) -> Document:
        """
        Parse a Box Notes file from disk.

        Args:
            file_path: Path to .boxnote file

        Returns:
            Document object with parsed content

        Raises:
            FileNotFoundError: If file doesn't exist
            JSONDecodeError: If file contains invalid JSON
            ParsingError: If parsing fails
        """
        import json
        from pathlib import Path

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Box Notes file not found: {file_path}")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return self.parse(data)
