"""Data models for Box Notes intermediate representation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class BlockType(Enum):
    """Types of content blocks in a document."""

    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE_BLOCK = "code_block"
    BLOCKQUOTE = "blockquote"
    LIST = "list"
    LIST_ITEM = "list_item"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    HORIZONTAL_RULE = "hr"
    IMAGE = "image"


class ListType(Enum):
    """Types of lists."""

    BULLET = "bullet"
    ORDERED = "ordered"
    CHECK = "check"


class FormatType(Enum):
    """Box Notes format versions."""

    OLD = "old"  # Pre-August 2022
    NEW = "new"  # Post-August 2022


@dataclass
class TextAttributes:
    """Formatting attributes for text spans."""

    bold: bool = False
    italic: bool = False
    code: bool = False
    underline: bool = False
    strike: bool = False
    link: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    highlight: Optional[str] = None

    def is_empty(self) -> bool:
        """Check if any formatting is applied."""
        return not (
            self.bold
            or self.italic
            or self.code
            or self.underline
            or self.strike
            or self.link
            or self.color
            or self.size
            or self.highlight
        )


@dataclass
class TextSpan:
    """A span of text with consistent formatting."""

    text: str
    attributes: TextAttributes = field(default_factory=TextAttributes)

    def __post_init__(self) -> None:
        """Validate text span."""
        if not isinstance(self.text, str):
            raise TypeError("TextSpan.text must be a string")
        if not isinstance(self.attributes, TextAttributes):
            raise TypeError("TextSpan.attributes must be a TextAttributes instance")


@dataclass
class Block:
    """A block-level element in the document."""

    type: BlockType
    content: List[TextSpan] = field(default_factory=list)
    children: List["Block"] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Type-specific attributes
    heading_level: Optional[int] = None  # For headings: 1, 2, or 3
    list_type: Optional[ListType] = None  # For list blocks
    checked: Optional[bool] = None  # For check list items

    # Image-specific attributes
    image_url: Optional[str] = None  # Image URL or data URI
    image_path: Optional[str] = None  # Path to extracted image file
    image_alt: Optional[str] = None  # Alt text for image
    image_title: Optional[str] = None  # Title for image

    def __post_init__(self) -> None:
        """Validate block."""
        if not isinstance(self.type, BlockType):
            raise TypeError("Block.type must be a BlockType instance")

        # Validate heading level
        if self.type == BlockType.HEADING:
            if self.heading_level is None or self.heading_level not in (1, 2, 3):
                raise ValueError("Heading blocks must have heading_level of 1, 2, or 3")

        # Validate list type
        if self.type == BlockType.LIST:
            if self.list_type is None:
                raise ValueError("List blocks must have a list_type")

    def get_text(self) -> str:
        """Get all text content from this block (excluding children)."""
        return "".join(span.text for span in self.content)

    def has_children(self) -> bool:
        """Check if block has children."""
        return len(self.children) > 0


@dataclass
class Document:
    """A complete Box Notes document."""

    blocks: List[Block] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate document."""
        if not isinstance(self.blocks, list):
            raise TypeError("Document.blocks must be a list")
        for block in self.blocks:
            if not isinstance(block, Block):
                raise TypeError("All items in Document.blocks must be Block instances")

    def get_text(self) -> str:
        """Get all text content from the document."""
        result = []
        for block in self.blocks:
            result.append(block.get_text())
            for child in block.children:
                result.append(child.get_text())
        return "\n".join(result)

    def block_count(self) -> int:
        """Count total number of blocks (including children)."""

        def count_blocks(blocks: List[Block]) -> int:
            total = len(blocks)
            for block in blocks:
                total += count_blocks(block.children)
            return total

        return count_blocks(self.blocks)
