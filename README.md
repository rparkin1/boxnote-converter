# Box Notes Converter

Convert Box Notes files (`.boxnote`) to Markdown or plain text format.

Box Notes uses a proprietary JSON format that changed in August 2022. This tool automatically detects and converts both the old format (pre-August 2022) and new format (post-August 2022) to standard Markdown or clean plain text.

## Features

- **Automatic format detection** - Works with both old and new Box Notes formats
- **Multiple output formats** - Convert to Markdown (GFM) or plain text
- **Comprehensive formatting support** - Handles headings, lists, tables, code blocks, links, and inline formatting
- **Command-line interface** - Simple CLI for batch conversion
- **Local processing** - No API keys or authentication required

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the package
uv pip install boxnotes
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/boxnotes.git
cd boxnotes

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"
```

## Quick Start

```bash
# Convert a single Box Notes file to Markdown (default)
boxnotes convert myfile.boxnote

# Convert all .boxnote files in a directory
boxnotes batch-convert ~/BoxNotes/

# Convert to plain text
boxnotes convert myfile.boxnote -f text

# Specify output file
boxnotes convert myfile.boxnote -o output.md

# Batch convert with recursive subdirectory processing
boxnotes batch-convert ~/BoxNotes/ --recursive -o ~/Converted/

# Convert to both formats at once
boxnotes convert myfile.boxnote -f both

# Show verbose output
boxnotes convert myfile.boxnote -v
```

## Usage

### Basic Conversion

Convert a Box Notes file to Markdown:

```bash
boxnotes convert notes.boxnote
```

This creates `notes.md` in the same directory.

### Output Formats

Choose your output format with `-f` or `--format`:

```bash
# Markdown (default)
boxnotes convert notes.boxnote -f markdown

# Plain text
boxnotes convert notes.boxnote -f text

# Both formats
boxnotes convert notes.boxnote -f both
```

### Output File

Specify a custom output path with `-o` or `--output`:

```bash
boxnotes convert notes.boxnote -o ~/Documents/converted.md
```

### Format Detection

By default, the tool automatically detects whether your file is old or new format.

You can force a specific parser if needed:

```bash
# Force old format parser (pre-August 2022)
boxnotes convert notes.boxnote --force-old

# Force new format parser (post-August 2022)
boxnotes convert notes.boxnote --force-new
```

### Verbose Mode

See detailed conversion information with `-v` or `--verbose`:

```bash
boxnotes convert notes.boxnote -v
```

Output:
```
Reading Box Notes file: notes.boxnote
Detected format: new
Parsing document with new format parser
Parsed 15 blocks
Extracting image: company-logo
  Saved to: notes_images/image_000_a1b2c3d4e5f6.png
Extracting image: screenshot
  Saved to: notes_images/image_001_f6e5d4c3b2a1.png
Extracted 2 image(s) to notes_images
Converting to markdown
Writing output to: notes.md
Conversion complete!
```

### Image Extraction

By default, embedded images (base64-encoded data URIs) are automatically extracted and saved as separate image files:

```bash
# Extract images (default behavior)
boxnotes convert notes.boxnote

# Disable image extraction
boxnotes convert notes.boxnote --no-extract-images

# Specify custom images directory
boxnotes convert notes.boxnote --images-dir ./my-images
```

**Image Handling:**
- Embedded images (data URIs) are extracted to `{filename}_images/` directory
- External images stored in Box Notes Images directory are automatically copied
- External image URLs (http/https) are preserved as-is in the output
- Image filenames are generated from content hash to avoid duplicates
- Alt text and titles are preserved in the markdown output
- In plain text format, images appear as `[Image: description] (url)`

**Box Notes Images Directory:**

Box Notes stores some images externally in a special directory structure:
```
MyBoxNotes/
├── 2020 Roadmap.boxnote
└── Box Notes Images/
    └── 2020 Roadmap Images/
        └── Screen Shot 2019-10-02 at 12.57.14 PM.png
```

The converter automatically detects and copies these external images to the output images directory.

**Example:**

Input Box Note contains:
- `data:image/png;base64,iVBORw0...` (embedded image)
- `https://example.com/logo.png` (external URL)

Output markdown:
```markdown
![Screenshot](notes_images/image_000_abc123.png)

![Company Logo](https://example.com/logo.png)
```

### Batch Conversion

Convert all `.boxnote` files in a directory with the `batch-convert` command:

```bash
# Convert all .boxnote files in a directory
boxnotes batch-convert ~/BoxNotes/

# Convert with custom output directory
boxnotes batch-convert ~/BoxNotes/ -o ~/Converted/

# Recursively process subdirectories
boxnotes batch-convert ~/BoxNotes/ --recursive

# Convert to plain text format
boxnotes batch-convert ~/BoxNotes/ -f text

# Convert to both formats
boxnotes batch-convert ~/BoxNotes/ -f both

# Verbose output to see progress
boxnotes batch-convert ~/BoxNotes/ -v

# Extract images (default behavior)
boxnotes batch-convert ~/BoxNotes/ --extract-images

# Disable image extraction
boxnotes batch-convert ~/BoxNotes/ --no-extract-images

# Use custom directory for all images
boxnotes batch-convert ~/BoxNotes/ --images-dir ./all_images
```

**Image Handling in Batch Mode:**
- Embedded images are extracted by default to `{filename}_images/` next to each output file
- External images from Box Notes Images directories are automatically copied
- Use `--images-dir` to save all images to a single centralized directory
- Use `--no-extract-images` to skip image extraction entirely
- Progress shows image extraction and copying for each file in verbose mode

**Features:**
- Automatically finds all `.boxnote` files in a directory
- Preserves original `.boxnote` files (never deletes them)
- Optional recursive processing of subdirectories
- **Image extraction** - automatically extracts embedded images and copies external images from Box Notes Images directories
- Custom images directory option for centralized image storage
- Progress tracking with file count and success/failure summary
- Error handling - continues processing even if some files fail
- Preserves directory structure when using output directory with `--recursive`

**Example output:**
```
Found 5 .boxnote file(s)

[1/5] Processing: note1.boxnote
  ✓ Converted successfully

[2/5] Processing: note2.boxnote
  ✓ Converted successfully

...

==================================================
Batch conversion complete!
  Total files: 5
  Successful: 5
  Failed: 0
```

## Supported Features

### Text Formatting

- **Bold** text
- *Italic* text
- ***Bold and italic***
- `Inline code`
- ~~Strikethrough~~
- [Links](https://example.com)

### Block Elements

- Headings (H1, H2, H3)
- Paragraphs
- Code blocks
- Blockquotes
- Horizontal rules
- Bullet lists
- Ordered lists
- Check lists (task lists)
- Tables
- **Images** (embedded and external)

### Image Support

Box Notes converter can extract and handle embedded images:

- **Data URIs**: Base64-encoded images are extracted and saved as separate files
- **External URLs**: HTTP/HTTPS image URLs are preserved in the output
- **Alt text**: Image descriptions are maintained
- **Automatic extraction**: Images are extracted by default to a `{filename}_images/` directory
- **Custom output**: Specify a custom directory for extracted images

### Lists

The tool supports nested lists with proper indentation:

```markdown
- Level 1 item
  - Level 2 item
    - Level 3 item
```

### Tables

Tables are converted to GitHub Flavored Markdown:

```markdown
| Header 1 | Header 2 |
| -------- | -------- |
| Cell 1   | Cell 2   |
```

In plain text format, tables use tab-separated values for easy import into spreadsheets.

## Box Notes Formats

### Old Format (Pre-August 2022)

The old format uses an "atext" structure with compressed attribute strings:

```json
{
  "atext": {
    "text": "Hello world\n",
    "attribs": "*0+c|1+1",
    "pool": {
      "numToAttrib": {
        "0": ["font-size-medium", "true"]
      }
    }
  }
}
```

This tool handles the complex decompression of these attribute strings automatically.

### New Format (Post-August 2022)

The new format uses a ProseMirror-like JSON structure:

```json
{
  "doc": {
    "type": "doc",
    "content": [
      {
        "type": "paragraph",
        "content": [
          {
            "type": "text",
            "text": "Hello world"
          }
        ]
      }
    ]
  }
}
```

The tool recursively parses the content tree and converts all supported node types.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=boxnotes --cov-report=html

# Run specific test file
pytest tests/test_cli.py -v

# Run specific test
pytest tests/test_cli.py::test_convert_old_format_to_markdown -v
```

### Code Quality

```bash
# Format code
black boxnotes tests

# Lint code
ruff check boxnotes tests

# Type check
mypy boxnotes

# Or use the Makefile
make format
make lint
make typecheck
```

### Makefile Commands

The project includes a Makefile with common commands:

```bash
make install      # Install in editable mode
make test         # Run tests with coverage
make format       # Format code with black
make lint         # Lint with ruff
make typecheck    # Type check with mypy
make clean        # Remove build artifacts
make help         # Show all commands
```

## Project Structure

```
boxnotes/
├── boxnotes/              # Main package
│   ├── cli.py            # Command-line interface
│   ├── detector.py       # Format detection
│   ├── models.py         # Data models
│   ├── exceptions.py     # Custom exceptions
│   ├── parsers/          # Box Notes parsers
│   │   ├── old_format.py # Pre-Aug 2022 parser
│   │   └── new_format.py # Post-Aug 2022 parser
│   ├── converters/       # Output converters
│   │   ├── markdown.py   # Markdown converter
│   │   └── plaintext.py  # Plain text converter
│   └── utils/            # Utilities
│       ├── attribs.py    # Attribute decompression
│       └── images.py     # Image extraction and handling
├── tests/                # Test suite
└── pyproject.toml        # Project configuration
```

## Troubleshooting

### "Unknown Box Notes format" Error

If you see this error, your file may be corrupted or not a valid Box Notes file. Try:

1. Opening the file in a text editor to verify it's valid JSON
2. Re-downloading the file from Box
3. Using `--force-old` or `--force-new` to force a specific parser

### Missing Formatting

Some advanced formatting (font colors, highlights, font sizes) is not preserved in Markdown or plain text output, as these formats don't support all Box Notes features.

### Empty Output

If the output file is empty:

1. Check that the input file has content using `cat myfile.boxnote`
2. Run with `-v` to see detailed parsing information
3. Check for any error messages

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`make test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Inspired by [boxnotes2html](https://github.com/alexwennerberg/boxnotes2html) and [boxtools](https://github.com/jessepov/boxtools)
- Uses [Click](https://click.palletsprojects.com/) for the CLI interface
- Built with [uv](https://github.com/astral-sh/uv) for fast package management

## Support

- **Issues**: Report bugs at https://github.com/yourusername/boxnotes/issues
- **Questions**: Open a discussion at https://github.com/yourusername/boxnotes/discussions
