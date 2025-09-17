# Scrivener to Markdown Converter

A Python tool to convert Scrivener (.scriv) projects to clean, structured Markdown format. Preserves the hierarchical structure of your Scrivener project while extracting readable text content from RTF files.

## Features

- **Preserves Project Structure**: Maintains the hierarchical folder/document organization from Scrivener
- **RTF to Markdown Conversion**: Extracts clean text from RTF format with proper heading levels
- **Metadata Preservation**: Includes synopsis and notes from your Scrivener documents
- **Flexible Output**: Generate single consolidated files or preserve folder structure
- **Safe Processing**: Handles missing files gracefully and provides clear error messages

## Quick Start

```bash
# Basic conversion
python3 scrivener_to_markdown.py "/path/to/YourProject.scriv"

# Specify output directory
python3 scrivener_to_markdown.py "/path/to/YourProject.scriv" "output_folder"

# Limit conversion for testing (useful for large projects)
python3 scrivener_to_markdown.py "/path/to/YourProject.scriv" "test_output" --limit 5
```

## Installation

No additional dependencies required - uses only Python standard library modules:
- `xml.etree.ElementTree` for parsing .scrivx files
- `pathlib` for file operations
- `re` for RTF processing

## How It Works

### Scrivener Project Structure
Scrivener projects (.scriv) are actually folders containing:
- **ProjectName.scrivx**: XML file with project structure and metadata
- **Files/Data/**: Folder containing document content in UUID-named subfolders
- **Settings/**: Project settings and preferences
- **QuickLook/**: Preview files

### Conversion Process
1. **Parse Structure**: Reads the .scrivx XML file to understand document hierarchy
2. **Extract Content**: Processes each document's RTF content files
3. **Convert RTF**: Strips RTF formatting to extract clean text
4. **Generate Markdown**: Creates properly structured markdown with headings
5. **Preserve Metadata**: Includes synopsis and notes as appropriate

### Output Format
```markdown
# Project Name
*Converted from Scrivener project*

## Chapter/Folder Name

### Document Title

**Synopsis:** Document synopsis if available

Document content goes here...

**Notes:**
Document notes if available
```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `scriv_path` | Path to .scriv project (required) | `"/Users/you/Documents/Novel.scriv"` |
| `output_dir` | Output directory (optional) | `"converted_markdown"` |
| `--limit N` | Limit to first N documents for testing | `--limit 10` |

## RTF Processing

The converter includes a basic RTF to plain text processor that:
- Removes RTF control sequences (`\command`, `{`, `}`)
- Converts RTF line breaks to markdown
- Cleans up excessive whitespace
- Preserves paragraph structure

**Note**: Complex RTF formatting (tables, images, etc.) may not convert perfectly. Review output for any formatting artifacts.

## Examples

### Basic Novel Conversion
```bash
python3 scrivener_to_markdown.py "/Users/author/Documents/MyNovel.scriv"
# Creates: MyNovel_markdown/MyNovel.md
```

### Academic Paper with Custom Output
```bash
python3 scrivener_to_markdown.py "/Users/researcher/Thesis.scriv" "thesis_draft"
# Creates: thesis_draft/Thesis.md
```

### Testing Large Project
```bash
python3 scrivener_to_markdown.py "/Users/author/EpicSaga.scriv" "preview" --limit 3
# Creates: preview/EpicSaga.md (first 3 documents only)
```

## File Structure After Conversion

```
output_directory/
└── ProjectName.md          # Complete converted project
```

## Troubleshooting

### Common Issues

**"Project file not found"**
- Ensure you're pointing to the .scriv folder, not a file inside it
- Check that the .scrivx file exists inside the .scriv folder

**"No content extracted"**
- Some Scrivener documents may be empty or contain only formatting
- Check the original project in Scrivener to verify content exists

**"RTF formatting artifacts"**
- Complex formatting may leave artifacts like `93` or `94` characters
- Manual cleanup may be needed for heavily formatted documents

### Performance Notes
- Large projects (>100 documents) may take several minutes to process
- Use `--limit` flag to test conversion on a subset first
- RTF processing is the most time-consuming step

## Technical Details

### Supported Scrivener Versions
- Tested with Scrivener 3.x projects
- Should work with Scrivener 2.x (different XML structure may need adjustments)

### Document Types Processed
- Text documents (main content)
- Folders (become heading levels)
- Synopsis files (.txt)
- Notes files (.rtf)

### Files Ignored
- Image files (.png, .jpg, etc.)
- PDF attachments
- Audio files
- Research materials in non-text formats

## Development

### Code Structure
- `ScrivenerDocument`: Represents individual documents with hierarchy
- `ScrivenerConverter`: Main conversion logic
- `strip_rtf()`: RTF to plain text processing
- `read_file_safe()`: Safe file reading with error handling

### Contributing
Feel free to improve the RTF processing, add support for more file types, or enhance the markdown output formatting.

## License

This tool is provided as-is for personal and educational use. No warranty implied.

---

*Created for converting Scrivener projects to markdown format while preserving structure and content.*