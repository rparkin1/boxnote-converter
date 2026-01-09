"""Tests for CLI interface."""

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from boxnotes.cli import cli


def test_convert_old_format_to_markdown(tmp_path):
    """Test converting old format file to markdown."""
    # Create test file with old format
    test_file = tmp_path / "test.boxnote"
    test_data = {
        "atext": {
            "text": "Hello world\n",
            "attribs": "*0+c|1+1",
            "pool": {
                "numToAttrib": {
                    "0": ["font-size-medium", "true"],
                }
            },
        }
    }

    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run CLI
    runner = CliRunner()
    result = runner.invoke(
        cli, ["convert", str(test_file), "-o", str(tmp_path / "output.md")]
    )

    assert result.exit_code == 0
    assert (tmp_path / "output.md").exists()

    # Verify output content
    output_content = (tmp_path / "output.md").read_text()
    assert "Hello world" in output_content


def test_convert_new_format_to_markdown(tmp_path):
    """Test converting new format file to markdown."""
    # Create test file with new format
    test_file = tmp_path / "test.boxnote"
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Hello "},
                        {
                            "type": "text",
                            "text": "world",
                            "marks": [{"type": "bold"}],
                        },
                    ],
                }
            ],
        }
    }

    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run CLI
    runner = CliRunner()
    result = runner.invoke(
        cli, ["convert", str(test_file), "-o", str(tmp_path / "output.md")]
    )

    assert result.exit_code == 0
    assert (tmp_path / "output.md").exists()

    # Verify output content
    output_content = (tmp_path / "output.md").read_text()
    assert "Hello" in output_content
    assert "world" in output_content
    assert "**world**" in output_content  # Bold formatting


def test_convert_to_plain_text(tmp_path):
    """Test converting to plain text format."""
    test_file = tmp_path / "test.boxnote"
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": "Title"}],
                }
            ],
        }
    }

    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run CLI with text format
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["convert", str(test_file), "-f", "text", "-o", str(tmp_path / "output.txt")],
    )

    assert result.exit_code == 0
    assert (tmp_path / "output.txt").exists()

    # Verify output content has underline style heading
    output_content = (tmp_path / "output.txt").read_text()
    assert "Title" in output_content
    assert "=====" in output_content  # Level 1 heading underline


def test_convert_both_formats(tmp_path):
    """Test converting to both markdown and text."""
    test_file = tmp_path / "test.boxnote"
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Test content"}],
                }
            ],
        }
    }

    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run CLI with both format
    runner = CliRunner()
    result = runner.invoke(cli, ["convert", str(test_file), "-f", "both"])

    assert result.exit_code == 0
    assert (tmp_path / "test.md").exists()
    assert (tmp_path / "test.txt").exists()

    # Verify both files have content
    md_content = (tmp_path / "test.md").read_text()
    txt_content = (tmp_path / "test.txt").read_text()
    assert "Test content" in md_content
    assert "Test content" in txt_content


def test_force_old_format_parser(tmp_path):
    """Test forcing old format parser."""
    test_file = tmp_path / "test.boxnote"
    test_data = {
        "atext": {
            "text": "Forced old\n",
            "attribs": "*0+a|1+1",
            "pool": {
                "numToAttrib": {
                    "0": ["font-size-medium", "true"],
                }
            },
        }
    }

    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run CLI with --force-old
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "convert",
            str(test_file),
            "--force-old",
            "-v",
            "-o",
            str(tmp_path / "output.md"),
        ],
    )

    assert result.exit_code == 0
    assert "Forcing old format parser" in result.output


def test_force_new_format_parser(tmp_path):
    """Test forcing new format parser."""
    test_file = tmp_path / "test.boxnote"
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Forced new"}],
                }
            ],
        }
    }

    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run CLI with --force-new
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "convert",
            str(test_file),
            "--force-new",
            "-v",
            "-o",
            str(tmp_path / "output.md"),
        ],
    )

    assert result.exit_code == 0
    assert "Forcing new format parser" in result.output


def test_verbose_mode(tmp_path):
    """Test verbose output mode."""
    test_file = tmp_path / "test.boxnote"
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Verbose test"}],
                }
            ],
        }
    }

    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run CLI with verbose
    runner = CliRunner()
    result = runner.invoke(
        cli, ["convert", str(test_file), "-v", "-o", str(tmp_path / "output.md")]
    )

    assert result.exit_code == 0
    assert "Reading Box Notes file" in result.output
    assert "Detected format" in result.output
    assert "Parsing document" in result.output
    assert "Converting to markdown" in result.output
    assert "Conversion complete" in result.output


def test_auto_generated_output_filename(tmp_path):
    """Test auto-generated output filename."""
    test_file = tmp_path / "myfile.boxnote"
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Auto output"}],
                }
            ],
        }
    }

    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run CLI without -o (should auto-generate filename)
    runner = CliRunner()
    result = runner.invoke(cli, ["convert", str(test_file)])

    assert result.exit_code == 0
    assert (tmp_path / "myfile.md").exists()


def test_error_file_not_found():
    """Test error handling for missing file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["convert", "/nonexistent/file.boxnote"])

    # Click returns exit code 2 for usage errors (invalid file path)
    assert result.exit_code == 2
    assert "does not exist" in result.output


def test_error_invalid_json(tmp_path):
    """Test error handling for invalid JSON."""
    test_file = tmp_path / "invalid.boxnote"
    test_file.write_text("not valid json")

    runner = CliRunner()
    result = runner.invoke(cli, ["convert", str(test_file)])

    assert result.exit_code == 1
    assert "Error" in result.output


def test_error_unknown_format(tmp_path):
    """Test error handling for unknown format."""
    test_file = tmp_path / "unknown.boxnote"
    test_data = {"unknown_field": "value"}

    with open(test_file, "w") as f:
        json.dump(test_data, f)

    runner = CliRunner()
    result = runner.invoke(cli, ["convert", str(test_file)])

    assert result.exit_code == 1


def test_cli_version():
    """Test CLI version command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Convert Box Notes files" in result.output


def test_convert_help():
    """Test convert subcommand help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["convert", "--help"])

    assert result.exit_code == 0
    assert "INPUT_FILE" in result.output
    assert "--output" in result.output
    assert "--format" in result.output
