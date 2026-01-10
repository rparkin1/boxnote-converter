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


def test_batch_convert_basic(tmp_path):
    """Test basic batch conversion of multiple files."""
    # Create test directory with multiple .boxnote files
    test_dir = tmp_path / "notes"
    test_dir.mkdir()

    # Create first test file (new format)
    test_file1 = test_dir / "note1.boxnote"
    test_data1 = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "First note"}],
                }
            ],
        }
    }
    with open(test_file1, "w") as f:
        json.dump(test_data1, f)

    # Create second test file (old format)
    test_file2 = test_dir / "note2.boxnote"
    test_data2 = {
        "atext": {
            "text": "Second note\n",
            "attribs": "*0+c|1+1",
            "pool": {"numToAttrib": {"0": ["font-size-medium", "true"]}},
        }
    }
    with open(test_file2, "w") as f:
        json.dump(test_data2, f)

    # Run batch conversion
    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", str(test_dir)])

    assert result.exit_code == 0
    assert "Found 2 .boxnote file(s)" in result.output
    assert "Batch conversion complete!" in result.output
    assert "Successful: 2" in result.output

    # Verify output files created in same directory
    assert (test_dir / "note1.md").exists()
    assert (test_dir / "note2.md").exists()

    # Verify original files preserved
    assert test_file1.exists()
    assert test_file2.exists()

    # Verify content
    note1_content = (test_dir / "note1.md").read_text()
    note2_content = (test_dir / "note2.md").read_text()
    assert "First note" in note1_content
    assert "Second note" in note2_content


def test_batch_convert_with_output_dir(tmp_path):
    """Test batch conversion with separate output directory."""
    # Create test directory with .boxnote files
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"

    test_file = input_dir / "test.boxnote"
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

    # Run batch conversion with output directory
    runner = CliRunner()
    result = runner.invoke(
        cli, ["batch-convert", str(input_dir), "-o", str(output_dir)]
    )

    assert result.exit_code == 0
    assert output_dir.exists()
    assert (output_dir / "test.md").exists()
    assert not (input_dir / "test.md").exists()  # Should not create in input dir

    # Verify original file preserved
    assert test_file.exists()


def test_batch_convert_recursive(tmp_path):
    """Test batch conversion with recursive subdirectory processing."""
    # Create nested directory structure
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    sub_dir1 = root_dir / "sub1"
    sub_dir1.mkdir()
    sub_dir2 = root_dir / "sub1" / "sub2"
    sub_dir2.mkdir()

    # Create files in different directories
    file1 = root_dir / "root.boxnote"
    file2 = sub_dir1 / "sub1.boxnote"
    file3 = sub_dir2 / "sub2.boxnote"

    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Test"}],
                }
            ],
        }
    }

    for f in [file1, file2, file3]:
        with open(f, "w") as fp:
            json.dump(test_data, fp)

    # Run batch conversion with recursive flag
    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", str(root_dir), "--recursive"])

    assert result.exit_code == 0
    assert "Found 3 .boxnote file(s)" in result.output
    assert "Successful: 3" in result.output

    # Verify all files converted
    assert (root_dir / "root.md").exists()
    assert (sub_dir1 / "sub1.md").exists()
    assert (sub_dir2 / "sub2.md").exists()

    # Verify original files preserved
    assert file1.exists()
    assert file2.exists()
    assert file3.exists()


def test_batch_convert_recursive_with_output_dir(tmp_path):
    """Test recursive batch conversion preserving directory structure."""
    # Create nested directory structure
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    sub_dir = input_dir / "subfolder"
    sub_dir.mkdir()
    output_dir = tmp_path / "output"

    # Create files in different directories
    file1 = input_dir / "root.boxnote"
    file2 = sub_dir / "sub.boxnote"

    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Test"}],
                }
            ],
        }
    }

    for f in [file1, file2]:
        with open(f, "w") as fp:
            json.dump(test_data, fp)

    # Run recursive batch conversion with output directory
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["batch-convert", str(input_dir), "--recursive", "-o", str(output_dir)],
    )

    assert result.exit_code == 0

    # Verify directory structure preserved in output
    assert (output_dir / "root.md").exists()
    assert (output_dir / "subfolder" / "sub.md").exists()


def test_batch_convert_both_formats(tmp_path):
    """Test batch conversion to both markdown and text."""
    test_dir = tmp_path / "notes"
    test_dir.mkdir()

    test_file = test_dir / "test.boxnote"
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

    # Run batch conversion with both format
    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", str(test_dir), "-f", "both"])

    assert result.exit_code == 0
    assert (test_dir / "test.md").exists()
    assert (test_dir / "test.txt").exists()

    # Verify original file preserved
    assert test_file.exists()


def test_batch_convert_to_text_format(tmp_path):
    """Test batch conversion to plain text format."""
    test_dir = tmp_path / "notes"
    test_dir.mkdir()

    test_file = test_dir / "test.boxnote"
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

    # Run batch conversion to text
    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", str(test_dir), "-f", "text"])

    assert result.exit_code == 0
    assert (test_dir / "test.txt").exists()
    assert not (test_dir / "test.md").exists()

    # Verify content
    content = (test_dir / "test.txt").read_text()
    assert "Title" in content


def test_batch_convert_empty_directory(tmp_path):
    """Test batch conversion with directory containing no .boxnote files."""
    test_dir = tmp_path / "empty"
    test_dir.mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", str(test_dir)])

    assert result.exit_code == 0
    assert "No .boxnote files found" in result.output


def test_batch_convert_error_handling(tmp_path):
    """Test batch conversion with mixed valid and invalid files."""
    test_dir = tmp_path / "notes"
    test_dir.mkdir()

    # Create valid file
    valid_file = test_dir / "valid.boxnote"
    valid_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Valid"}],
                }
            ],
        }
    }
    with open(valid_file, "w") as f:
        json.dump(valid_data, f)

    # Create invalid file (bad JSON)
    invalid_file = test_dir / "invalid.boxnote"
    invalid_file.write_text("not valid json")

    # Run batch conversion
    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", str(test_dir)])

    assert result.exit_code == 1  # Should exit with error due to failures
    assert "Successful: 1" in result.output
    assert "Failed: 1" in result.output

    # Verify valid file was converted
    assert (test_dir / "valid.md").exists()

    # Verify original files preserved
    assert valid_file.exists()
    assert invalid_file.exists()


def test_batch_convert_verbose_mode(tmp_path):
    """Test batch conversion with verbose output."""
    test_dir = tmp_path / "notes"
    test_dir.mkdir()

    test_file = test_dir / "test.boxnote"
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Test"}],
                }
            ],
        }
    }
    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run batch conversion with verbose flag
    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", str(test_dir), "-v"])

    assert result.exit_code == 0
    assert "Reading Box Notes file" in result.output
    assert "Detected format" in result.output
    assert "Parsing document" in result.output
    assert "Converting to markdown" in result.output


def test_batch_convert_force_format(tmp_path):
    """Test batch conversion with forced format parser."""
    test_dir = tmp_path / "notes"
    test_dir.mkdir()

    test_file = test_dir / "test.boxnote"
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Test"}],
                }
            ],
        }
    }
    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run batch conversion with forced new format
    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", str(test_dir), "--force-new", "-v"])

    assert result.exit_code == 0
    assert "Forcing new format parser" in result.output


def test_batch_convert_help():
    """Test batch-convert subcommand help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", "--help"])

    assert result.exit_code == 0
    assert "DIRECTORY" in result.output
    assert "--output-dir" in result.output
    assert "--recursive" in result.output
    assert "Original .boxnote" in result.output
    assert "preserved" in result.output
    assert "--extract-images" in result.output
    assert "--images-dir" in result.output


def test_batch_convert_with_images(tmp_path):
    """Test batch conversion with image extraction."""
    test_dir = tmp_path / "notes"
    test_dir.mkdir()

    # Create test file with an image
    test_file = test_dir / "with_image.boxnote"
    # 1x1 transparent PNG data URI
    data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Text before image"}],
                },
                {
                    "type": "image",
                    "attrs": {
                        "src": data_uri,
                        "alt": "Test Image",
                    },
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Text after image"}],
                },
            ],
        }
    }
    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run batch conversion with image extraction
    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", str(test_dir), "-v"])

    assert result.exit_code == 0
    assert "Extracting image: Test Image" in result.output
    assert "Total: 1 image(s)" in result.output

    # Verify markdown file created
    md_file = test_dir / "with_image.md"
    assert md_file.exists()

    # Verify images directory created
    images_dir = test_dir / "with_image_images"
    assert images_dir.exists()

    # Verify image file extracted
    image_files = list(images_dir.glob("*.png"))
    assert len(image_files) == 1

    # Verify markdown references the image
    md_content = md_file.read_text()
    assert "![Test Image]" in md_content
    assert "with_image_images/" in md_content


def test_batch_convert_no_extract_images(tmp_path):
    """Test batch conversion with image extraction disabled."""
    test_dir = tmp_path / "notes"
    test_dir.mkdir()

    # Create test file with an image
    test_file = test_dir / "with_image.boxnote"
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "image",
                    "attrs": {
                        "src": "https://example.com/image.png",
                        "alt": "External Image",
                    },
                },
            ],
        }
    }
    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run batch conversion with image extraction disabled
    runner = CliRunner()
    result = runner.invoke(cli, ["batch-convert", str(test_dir), "--no-extract-images"])

    assert result.exit_code == 0

    # Verify no images directory created
    images_dir = test_dir / "with_image_images"
    assert not images_dir.exists()

    # Verify markdown still has external URL
    md_file = test_dir / "with_image.md"
    md_content = md_file.read_text()
    assert "https://example.com/image.png" in md_content


def test_batch_convert_custom_images_dir(tmp_path):
    """Test batch conversion with custom images directory."""
    test_dir = tmp_path / "notes"
    test_dir.mkdir()
    custom_images_dir = tmp_path / "all_images"

    # Create test file with an image
    test_file = test_dir / "note.boxnote"
    data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    test_data = {
        "doc": {
            "type": "doc",
            "content": [
                {
                    "type": "image",
                    "attrs": {"src": data_uri, "alt": "Image"},
                },
            ],
        }
    }
    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Run batch conversion with custom images directory
    runner = CliRunner()
    result = runner.invoke(
        cli, ["batch-convert", str(test_dir), "--images-dir", str(custom_images_dir)]
    )

    assert result.exit_code == 0

    # Verify custom images directory created
    assert custom_images_dir.exists()

    # Verify image file in custom directory
    image_files = list(custom_images_dir.glob("*.png"))
    assert len(image_files) >= 1
