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
from boxnotes.models import FormatType
from boxnotes.parsers.new_format import NewFormatParser
from boxnotes.parsers.old_format import OldFormatParser


@click.group()
@click.version_option(version="0.1.0", prog_name="boxnotes")
def cli():
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
):
    """
    Convert a Box Notes file to Markdown or plain text.

    INPUT_FILE: Path to the .boxnote file to convert
    """
    try:
        # Read input file
        if verbose:
            click.echo(f"Reading Box Notes file: {input_file}")

        with open(input_file, "r", encoding="utf-8") as f:
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
            click.echo(
                "Error: Auto-detection disabled but no format forced", err=True
            )
            sys.exit(1)

        # Parse document
        if verbose:
            click.echo(f"Parsing document with {detected_format.value} format parser")

        if detected_format == FormatType.OLD:
            parser = OldFormatParser()
        else:
            parser = NewFormatParser()

        document = parser.parse(data)

        if verbose:
            click.echo(f"Parsed {len(document.blocks)} blocks")

        # Convert to requested format(s)
        if output_format == "both":
            _convert_both_formats(
                document, input_file, output, verbose
            )
        else:
            _convert_single_format(
                document, input_file, output, output_format, verbose
            )

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
    document,
    input_file: Path,
    output: Optional[Path],
    output_format: str,
    verbose: bool,
):
    """Convert document to a single output format."""
    # Create converter
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
    document,
    input_file: Path,
    output: Optional[Path],
    verbose: bool,
):
    """Convert document to both Markdown and plain text."""
    if output:
        click.echo(
            "Warning: --output is ignored when using --format both", err=True
        )

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


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
