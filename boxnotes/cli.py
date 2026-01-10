"""Command-line interface for Box Notes converter."""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from boxnotes.converters.markdown import MarkdownConverter
from boxnotes.converters.plaintext import PlainTextConverter
from boxnotes.detector import detect_format
from boxnotes.exceptions import BoxNotesError, ConversionError, ParsingError
from boxnotes.models import Document, FormatType
from boxnotes.parsers.base import BoxNoteParser
from boxnotes.parsers.new_format import NewFormatParser
from boxnotes.parsers.old_format import OldFormatParser


@click.group()
@click.version_option(version="0.1.0", prog_name="boxnotes")
def cli() -> None:
    """Convert Box Notes files to Markdown or plain text."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout or auto-generated)",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["markdown", "text", "both"], case_sensitive=False),
    default="markdown",
    help="Output format (default: markdown)",
)
@click.option(
    "--detect/--no-detect",
    "auto_detect",
    default=True,
    help="Auto-detect Box Notes format (default: enabled)",
)
@click.option(
    "--force-old",
    "force_format",
    flag_value="old",
    help="Force old format parser (pre-August 2022)",
)
@click.option(
    "--force-new",
    "force_format",
    flag_value="new",
    help="Force new format parser (post-August 2022)",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Show verbose output during conversion"
)
def convert(
    input_file: Path,
    output: Optional[Path],
    output_format: str,
    auto_detect: bool,
    force_format: Optional[str],
    verbose: bool,
) -> None:
    """
    Convert a Box Notes file to Markdown or plain text.

    INPUT_FILE: Path to the .boxnote file to convert
    """
    try:
        # Read input file
        if verbose:
            click.echo(f"Reading Box Notes file: {input_file}")

        with open(input_file, encoding="utf-8") as f:
            data = json.load(f)

        # Detect or force format
        if force_format:
            if force_format == "old":
                detected_format = FormatType.OLD
                if verbose:
                    click.echo("Forcing old format parser")
            else:
                detected_format = FormatType.NEW
                if verbose:
                    click.echo("Forcing new format parser")
        elif auto_detect:
            detected_format = detect_format(data)
            if verbose:
                click.echo(f"Detected format: {detected_format.value}")
        else:
            click.echo("Error: Auto-detection disabled but no format forced", err=True)
            sys.exit(1)

        # Parse document
        if verbose:
            click.echo(f"Parsing document with {detected_format.value} format parser")

        parser: BoxNoteParser
        if detected_format == FormatType.OLD:
            parser = OldFormatParser()
        else:
            parser = NewFormatParser()

        document = parser.parse(data)

        if verbose:
            click.echo(f"Parsed {len(document.blocks)} blocks")

        # Convert to requested format(s)
        if output_format == "both":
            _convert_both_formats(document, input_file, output, verbose)
        else:
            _convert_single_format(document, input_file, output, output_format, verbose)

        if verbose:
            click.echo("Conversion complete!")

    except FileNotFoundError:
        click.echo(f"Error: File not found: {input_file}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in {input_file}: {e}", err=True)
        sys.exit(1)
    except ParsingError as e:
        click.echo(f"Error parsing Box Notes file: {e}", err=True)
        sys.exit(1)
    except ConversionError as e:
        click.echo(f"Error converting document: {e}", err=True)
        sys.exit(1)
    except BoxNotesError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def _convert_single_format(
    document: Document,
    input_file: Path,
    output: Optional[Path],
    output_format: str,
    verbose: bool,
) -> None:
    """Convert document to a single output format."""
    # Create converter
    from boxnotes.converters.base import DocumentConverter

    converter: DocumentConverter
    if output_format == "markdown":
        converter = MarkdownConverter()
        extension = ".md"
    else:  # text
        converter = PlainTextConverter()
        extension = ".txt"

    # Convert
    if verbose:
        click.echo(f"Converting to {output_format}")

    result = converter.convert(document)

    # Determine output path
    if output:
        output_path = output
    else:
        # Auto-generate output filename
        output_path = input_file.with_suffix(extension)

    # Write or print output
    if output or output != Path("-"):
        if verbose:
            click.echo(f"Writing output to: {output_path}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        # Write to stdout
        click.echo(result)


def _convert_both_formats(
    document: Document,
    input_file: Path,
    output: Optional[Path],
    verbose: bool,
) -> None:
    """Convert document to both Markdown and plain text."""
    if output:
        click.echo("Warning: --output is ignored when using --format both", err=True)

    # Convert to Markdown
    if verbose:
        click.echo("Converting to Markdown")

    md_converter = MarkdownConverter()
    md_result = md_converter.convert(document)
    md_path = input_file.with_suffix(".md")

    if verbose:
        click.echo(f"Writing Markdown output to: {md_path}")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_result)

    # Convert to plain text
    if verbose:
        click.echo("Converting to plain text")

    txt_converter = PlainTextConverter()
    txt_result = txt_converter.convert(document)
    txt_path = input_file.with_suffix(".txt")

    if verbose:
        click.echo(f"Writing plain text output to: {txt_path}")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_result)

    click.echo(f"Created: {md_path}")
    click.echo(f"Created: {txt_path}")


@cli.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Output directory for converted files (default: same as input)",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["markdown", "text", "both"], case_sensitive=False),
    default="markdown",
    help="Output format (default: markdown)",
)
@click.option(
    "--recursive/--no-recursive",
    default=False,
    help="Recursively process subdirectories (default: disabled)",
)
@click.option(
    "--detect/--no-detect",
    "auto_detect",
    default=True,
    help="Auto-detect Box Notes format (default: enabled)",
)
@click.option(
    "--force-old",
    "force_format",
    flag_value="old",
    help="Force old format parser (pre-August 2022)",
)
@click.option(
    "--force-new",
    "force_format",
    flag_value="new",
    help="Force new format parser (post-August 2022)",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Show verbose output during conversion"
)
def batch_convert(
    directory: Path,
    output_dir: Optional[Path],
    output_format: str,
    recursive: bool,
    auto_detect: bool,
    force_format: Optional[str],
    verbose: bool,
) -> None:
    """
    Batch convert all Box Notes files in a directory.

    DIRECTORY: Path to directory containing .boxnote files

    This command finds all .boxnote files in the specified directory
    and converts them to the requested format(s). Original .boxnote
    files are preserved and never deleted.
    """
    try:
        # Find all .boxnote files
        boxnote_files = _find_boxnote_files(directory, recursive)

        if not boxnote_files:
            click.echo(f"No .boxnote files found in {directory}")
            return

        # Summary info
        click.echo(f"Found {len(boxnote_files)} .boxnote file(s)")
        if verbose:
            for f in boxnote_files:
                click.echo(f"  - {f}")

        # Create output directory if specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            if verbose:
                click.echo(f"Output directory: {output_dir}")

        # Process each file
        successful = 0
        failed = 0
        errors = []

        for idx, input_file in enumerate(boxnote_files, 1):
            click.echo(f"\n[{idx}/{len(boxnote_files)}] Processing: {input_file.name}")

            try:
                # Read input file
                if verbose:
                    click.echo(f"  Reading Box Notes file: {input_file}")

                with open(input_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Detect or force format
                if force_format:
                    if force_format == "old":
                        detected_format = FormatType.OLD
                        if verbose:
                            click.echo("  Forcing old format parser")
                    else:
                        detected_format = FormatType.NEW
                        if verbose:
                            click.echo("  Forcing new format parser")
                elif auto_detect:
                    detected_format = detect_format(data)
                    if verbose:
                        click.echo(f"  Detected format: {detected_format.value}")
                else:
                    click.echo(
                        "  Error: Auto-detection disabled but no format forced",
                        err=True,
                    )
                    failed += 1
                    errors.append((input_file.name, "No format specified"))
                    continue

                # Parse document
                if verbose:
                    click.echo(
                        f"  Parsing document with {detected_format.value} format parser"
                    )

                parser: BoxNoteParser
                if detected_format == FormatType.OLD:
                    parser = OldFormatParser()
                else:
                    parser = NewFormatParser()

                document = parser.parse(data)

                if verbose:
                    click.echo(f"  Parsed {len(document.blocks)} blocks")

                # Determine output location
                if output_dir:
                    # Preserve directory structure if recursive
                    if recursive:
                        relative_path = input_file.relative_to(directory)
                        output_base = (
                            output_dir / relative_path.parent / input_file.stem
                        )
                        # Create subdirectories if needed
                        output_base.parent.mkdir(parents=True, exist_ok=True)
                    else:
                        output_base = output_dir / input_file.stem
                else:
                    output_base = input_file.parent / input_file.stem

                # Convert to requested format(s)
                if output_format == "both":
                    _batch_convert_both_formats(document, output_base, verbose)
                else:
                    _batch_convert_single_format(
                        document, output_base, output_format, verbose
                    )

                successful += 1
                click.echo("  ✓ Converted successfully")

            except json.JSONDecodeError as e:
                failed += 1
                error_msg = f"Invalid JSON: {e}"
                errors.append((input_file.name, error_msg))
                click.echo(f"  ✗ Error: {error_msg}", err=True)
            except ParsingError as e:
                failed += 1
                error_msg = f"Parsing error: {e}"
                errors.append((input_file.name, error_msg))
                click.echo(f"  ✗ Error: {error_msg}", err=True)
            except ConversionError as e:
                failed += 1
                error_msg = f"Conversion error: {e}"
                errors.append((input_file.name, error_msg))
                click.echo(f"  ✗ Error: {error_msg}", err=True)
            except BoxNotesError as e:
                failed += 1
                error_msg = str(e)
                errors.append((input_file.name, error_msg))
                click.echo(f"  ✗ Error: {error_msg}", err=True)
            except Exception as e:
                failed += 1
                error_msg = f"Unexpected error: {e}"
                errors.append((input_file.name, error_msg))
                click.echo(f"  ✗ Error: {error_msg}", err=True)
                if verbose:
                    import traceback

                    traceback.print_exc()

        # Summary
        click.echo("\n" + "=" * 50)
        click.echo("Batch conversion complete!")
        click.echo(f"  Total files: {len(boxnote_files)}")
        click.echo(f"  Successful: {successful}")
        click.echo(f"  Failed: {failed}")

        if errors and verbose:
            click.echo("\nErrors:")
            for filename, error in errors:
                click.echo(f"  - {filename}: {error}")

        # Exit with error code if any conversions failed
        if failed > 0:
            sys.exit(1)

    except Exception as e:
        click.echo(f"Fatal error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def _find_boxnote_files(directory: Path, recursive: bool) -> list[Path]:
    """
    Find all .boxnote files in a directory.

    Args:
        directory: Directory to search
        recursive: Whether to search subdirectories

    Returns:
        List of paths to .boxnote files
    """
    if recursive:
        return sorted(directory.rglob("*.boxnote"))
    else:
        return sorted(directory.glob("*.boxnote"))


def _batch_convert_single_format(
    document: Document,
    output_base: Path,
    output_format: str,
    verbose: bool,
) -> None:
    """Convert document to a single output format for batch processing."""
    # Create converter
    from boxnotes.converters.base import DocumentConverter

    converter: DocumentConverter
    if output_format == "markdown":
        converter = MarkdownConverter()
        extension = ".md"
    else:  # text
        converter = PlainTextConverter()
        extension = ".txt"

    # Convert
    if verbose:
        click.echo(f"  Converting to {output_format}")

    result = converter.convert(document)

    # Write output
    output_path = output_base.with_suffix(extension)

    if verbose:
        click.echo(f"  Writing output to: {output_path}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)


def _batch_convert_both_formats(
    document: Document,
    output_base: Path,
    verbose: bool,
) -> None:
    """Convert document to both Markdown and plain text for batch processing."""
    # Convert to Markdown
    if verbose:
        click.echo("  Converting to Markdown")

    md_converter = MarkdownConverter()
    md_result = md_converter.convert(document)
    md_path = output_base.with_suffix(".md")

    if verbose:
        click.echo(f"  Writing Markdown output to: {md_path}")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_result)

    # Convert to plain text
    if verbose:
        click.echo("  Converting to plain text")

    txt_converter = PlainTextConverter()
    txt_result = txt_converter.convert(document)
    txt_path = output_base.with_suffix(".txt")

    if verbose:
        click.echo(f"  Writing plain text output to: {txt_path}")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_result)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
