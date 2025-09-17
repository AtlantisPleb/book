#!/usr/bin/env python3
"""
Scrivener to Markdown Converter

Converts Scrivener (.scriv) projects to markdown format.
Preserves the hierarchical structure and extracts text content from RTF files.
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple


def strip_rtf(rtf_content: str) -> str:
    """
    Improved RTF to plain text conversion.
    Removes RTF control sequences and extracts readable text with proper character mapping.
    """
    if not rtf_content.strip():
        return ""
    
    # Remove RTF header and formatting commands
    content = rtf_content
    
    # Remove RTF control sequences but preserve some formatting hints
    content = re.sub(r'\\[a-z]+\d*\s*', ' ', content)
    content = re.sub(r'\\[^a-z\s]', '', content)
    content = re.sub(r'[{}]', '', content)
    
    # Fix common RTF character encoding issues
    content = content.replace('92', "'")      # Apostrophe
    content = content.replace('93', '"')      # Left double quote
    content = content.replace('94', '"')      # Right double quote
    content = content.replace('97', '—')      # Em dash
    content = content.replace('85', '…')      # Ellipsis
    content = content.replace('96', "'")      # Left single quote
    content = content.replace('91', "'")      # Left single quote alternative
    
    # Convert RTF line breaks and paragraph breaks
    content = content.replace('\\\\', '\n')
    content = content.replace('\\\n', '\n')
    content = content.replace('\\par', '\n\n')
    
    # Clean up RTF spacing artifacts
    content = re.sub(r'-\d+', '', content)    # Remove negative spacing numbers like -720, -1440
    
    # Remove font declarations and formatting artifacts at start of lines
    content = re.sub(r'^[A-Za-z-]+;\s*', '', content, flags=re.MULTILINE)  # Remove font declarations
    content = re.sub(r'^\s*;\s*', '', content, flags=re.MULTILINE)  # Remove leftover semicolons
    
    content = re.sub(r'\s+', ' ', content)    # Normalize whitespace
    content = re.sub(r'^\s+', '', content, flags=re.MULTILINE)  # Remove leading spaces on lines
    
    # Clean up paragraph breaks
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    content = content.strip()
    
    return content


def read_file_safe(file_path: Path) -> str:
    """Safely read a file, returning empty string if file doesn't exist or can't be read."""
    try:
        if file_path.exists():
            return file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
    return ""


class ScrivenerDocument:
    """Represents a single document in a Scrivener project."""
    
    def __init__(self, uuid: str, title: str, doc_type: str, level: int = 0):
        self.uuid = uuid
        self.title = title
        self.doc_type = doc_type  # 'Text', 'Folder', 'DraftFolder'
        self.level = level
        self.content = ""
        self.synopsis = ""
        self.notes = ""
        self.children: List['ScrivenerDocument'] = []
    
    def to_markdown(self) -> str:
        """Convert document to markdown format."""
        md_lines = []
        
        # Add title with appropriate heading level
        if self.title and self.doc_type in ['Text', 'Folder', 'DraftFolder']:
            heading_level = min(self.level + 1, 6)  # Max heading level is 6
            md_lines.append(f"{'#' * heading_level} {self.title}")
            md_lines.append("")
        
        # Add synopsis if available
        if self.synopsis.strip():
            md_lines.append("**Synopsis:** " + self.synopsis.strip())
            md_lines.append("")
        
        # Add content
        if self.content.strip():
            md_lines.append(self.content.strip())
            md_lines.append("")
        
        # Add notes if available
        if self.notes.strip():
            md_lines.append("**Notes:**")
            md_lines.append("")
            md_lines.append(self.notes.strip())
            md_lines.append("")
        
        return "\n".join(md_lines)


class ScrivenerConverter:
    """Converts Scrivener projects to markdown."""
    
    def __init__(self, scriv_path: str):
        self.scriv_path = Path(scriv_path)
        self.project_name = self.scriv_path.stem
        self.scrivx_path = self.scriv_path / f"{self.project_name}.scrivx"
        self.data_path = self.scriv_path / "Files" / "Data"
        
        if not self.scriv_path.exists():
            raise FileNotFoundError(f"Scrivener project not found: {scriv_path}")
        if not self.scrivx_path.exists():
            raise FileNotFoundError(f"Project file not found: {self.scrivx_path}")
    
    def parse_project_structure(self) -> List[ScrivenerDocument]:
        """Parse the .scrivx file to extract project structure."""
        try:
            tree = ET.parse(self.scrivx_path)
            root = tree.getroot()
            
            # Find the Binder element
            binder = root.find('Binder')
            if binder is None:
                raise ValueError("No Binder element found in project file")
            
            documents = []
            self._parse_binder_items(binder, documents, 0)
            return documents
            
        except ET.ParseError as e:
            raise ValueError(f"Error parsing project file: {e}")
    
    def _parse_binder_items(self, parent_element, documents: List[ScrivenerDocument], level: int):
        """Recursively parse binder items."""
        for item in parent_element.findall('BinderItem'):
            uuid = item.get('UUID', '')
            doc_type = item.get('Type', 'Text')
            
            title_elem = item.find('Title')
            title = title_elem.text if title_elem is not None else f"Untitled ({uuid[:8]})"
            
            doc = ScrivenerDocument(uuid, title, doc_type, level)
            documents.append(doc)
            
            # Load content from data files
            self._load_document_content(doc)
            
            # Process children
            children_elem = item.find('Children')
            if children_elem is not None:
                self._parse_binder_items(children_elem, doc.children, level + 1)
    
    def _load_document_content(self, doc: ScrivenerDocument):
        """Load content from the document's data folder."""
        doc_folder = self.data_path / doc.uuid
        
        if not doc_folder.exists():
            return
        
        # Load main content
        content_rtf = doc_folder / "content.rtf"
        if content_rtf.exists():
            rtf_content = read_file_safe(content_rtf)
            doc.content = strip_rtf(rtf_content)
        
        # Load synopsis
        synopsis_file = doc_folder / "synopsis.txt"
        if synopsis_file.exists():
            doc.synopsis = read_file_safe(synopsis_file)
        
        # Load notes
        notes_file = doc_folder / "notes.rtf"
        if notes_file.exists():
            rtf_notes = read_file_safe(notes_file)
            doc.notes = strip_rtf(rtf_notes)
    
    def convert_to_markdown(self, output_dir: str = None, limit_files: int = None, separate_files: bool = False) -> str:
        """Convert the entire project to markdown."""
        if output_dir is None:
            output_dir = f"{self.project_name}_markdown"
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        documents = self.parse_project_structure()
        
        # Limit files if specified (for testing)
        if limit_files:
            documents = documents[:limit_files]
        
        if separate_files:
            # Create separate files maintaining folder structure
            self._create_separate_files(documents, output_path)
            return str(output_path)
        else:
            # Generate single markdown file
            markdown_content = []
            markdown_content.append(f"# {self.project_name}")
            markdown_content.append("")
            markdown_content.append(f"*Converted from Scrivener project*")
            markdown_content.append("")
            
            self._generate_markdown_recursive(documents, markdown_content)
            
            # Write main file
            main_file = output_path / f"{self.project_name}.md"
            main_file.write_text("\n".join(markdown_content), encoding='utf-8')
            
            return str(main_file)
    
    def _create_separate_files(self, documents: List[ScrivenerDocument], base_path: Path):
        """Create separate markdown files maintaining folder structure."""
        for doc in documents:
            if doc.doc_type == 'Folder' or doc.doc_type == 'DraftFolder':
                # Create folder
                folder_path = base_path / self._sanitize_filename(doc.title)
                folder_path.mkdir(exist_ok=True)
                
                # Create index file for the folder if it has content
                if doc.content.strip() or doc.synopsis.strip() or doc.notes.strip():
                    index_content = doc.to_markdown()
                    if index_content.strip():
                        index_file = folder_path / "README.md"
                        index_file.write_text(index_content, encoding='utf-8')
                
                # Process children in this folder
                if doc.children:
                    self._create_separate_files(doc.children, folder_path)
            
            elif doc.doc_type == 'Text':
                # Create individual markdown file
                filename = self._sanitize_filename(doc.title) + ".md"
                file_path = base_path / filename
                
                content = doc.to_markdown()
                if content.strip():
                    file_path.write_text(content, encoding='utf-8')
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = sanitized.strip().strip('.')
        
        # Handle empty or very long filenames
        if not sanitized:
            sanitized = "Untitled"
        elif len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized
    
    def _generate_markdown_recursive(self, documents: List[ScrivenerDocument], content: List[str]):
        """Recursively generate markdown for documents and their children."""
        for doc in documents:
            doc_md = doc.to_markdown()
            if doc_md.strip():
                content.append(doc_md)
            
            if doc.children:
                self._generate_markdown_recursive(doc.children, content)


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python scrivener_to_markdown.py <path_to_scriv_project> [output_dir] [--limit N] [--separate-files]")
        print("Example: python scrivener_to_markdown.py /path/to/project.scriv")
        print("  --separate-files: Create separate files in folders like Scrivener structure")
        print("  --limit N: Limit conversion to first N documents")
        sys.exit(1)
    
    scriv_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    
    # Check for flags
    limit_files = None
    separate_files = False
    
    if '--limit' in sys.argv:
        try:
            limit_idx = sys.argv.index('--limit')
            limit_files = int(sys.argv[limit_idx + 1])
        except (IndexError, ValueError):
            print("Error: --limit requires a number")
            sys.exit(1)
    
    if '--separate-files' in sys.argv:
        separate_files = True
    
    try:
        converter = ScrivenerConverter(scriv_path)
        output_path = converter.convert_to_markdown(output_dir, limit_files, separate_files)
        
        if separate_files:
            print(f"Conversion complete! Separate files created in: {output_path}")
        else:
            print(f"Conversion complete! Output written to: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()