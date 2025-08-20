#!/usr/bin/env python3
"""
Simple Markdown to PDF Converter
Uses reportlab for PDF generation - works without external system dependencies
"""
import os
import sys
from pathlib import Path
import argparse
from datetime import datetime
import re
import textwrap

class SimpleMarkdownToPDF:
    def __init__(self):
        self.reportlab_available = self._check_reportlab()
        
    def _check_reportlab(self):
        """Check if reportlab is available"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            return True
        except ImportError:
            return False
    
    def install_dependencies(self):
        """Install reportlab for PDF generation"""
        try:
            import subprocess
            print("📦 Installing reportlab for PDF conversion...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'reportlab'], check=True)
            print("✅ Reportlab installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation failed: {e}")
            return False
    
    def convert_markdown_to_pdf(self, md_file, pdf_file):
        """Convert markdown to PDF using reportlab"""
        if not self.reportlab_available:
            print("❌ Reportlab not available. Run with --install first.")
            return False
        
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import black, blue, gray
            
            # Read markdown content
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create PDF document
            doc = SimpleDocTemplate(str(pdf_file), pagesize=letter,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle('CustomTitle',
                                       parent=styles['Heading1'],
                                       fontSize=20,
                                       spaceAfter=30,
                                       textColor=blue)
            
            heading_style = ParagraphStyle('CustomHeading',
                                         parent=styles['Heading2'], 
                                         fontSize=14,
                                         spaceAfter=12,
                                         textColor=black,
                                         leftIndent=0)
            
            subheading_style = ParagraphStyle('CustomSubHeading',
                                            parent=styles['Heading3'],
                                            fontSize=12,
                                            spaceAfter=8,
                                            textColor=black)
            
            normal_style = ParagraphStyle('CustomNormal',
                                        parent=styles['Normal'],
                                        fontSize=10,
                                        spaceAfter=8,
                                        leftIndent=0)
            
            # Parse markdown content
            story = []
            lines = content.split('\\n')
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    story.append(Spacer(1, 6))
                    continue
                
                # Title (# Header)
                if line.startswith('# '):
                    text = line[2:].strip()
                    story.append(Paragraph(text, title_style))
                
                # Heading (## Header)
                elif line.startswith('## '):
                    text = line[3:].strip()
                    story.append(Spacer(1, 12))
                    story.append(Paragraph(text, heading_style))
                
                # Subheading (### Header)
                elif line.startswith('### '):
                    text = line[4:].strip()
                    story.append(Spacer(1, 8))
                    story.append(Paragraph(text, subheading_style))
                
                # Horizontal rule
                elif line.startswith('---'):
                    story.append(Spacer(1, 12))
                    story.append(Paragraph('_' * 80, normal_style))
                    story.append(Spacer(1, 12))
                
                # Bold text (**text**)
                elif '**' in line:
                    text = re.sub(r'\\*\\*(.*?)\\*\\*', r'<b>\\1</b>', line)
                    story.append(Paragraph(text, normal_style))
                
                # URLs and links
                elif 'http' in line:
                    # Convert URLs to clickable links
                    text = re.sub(r'(https?://[^\\s]+)', r'<link href="\\1">\\1</link>', line)
                    story.append(Paragraph(text, normal_style))
                
                # Regular paragraph
                else:
                    story.append(Paragraph(line, normal_style))
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"❌ PDF conversion failed: {e}")
            return False
    
    def convert_file(self, md_file, output_dir=None, custom_name=None):
        """Convert a single markdown file to PDF"""
        md_path = Path(md_file)
        
        if not md_path.exists():
            print(f"❌ File not found: {md_file}")
            return False
        
        # Determine output path
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = md_path.parent / 'pdf_exports'
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF filename
        if custom_name:
            pdf_name = f"{custom_name}.pdf"
        else:
            pdf_name = md_path.stem + ".pdf"
        
        pdf_file = output_path / pdf_name
        
        print(f"📄 Converting: {md_path.name} -> {pdf_name}")
        
        success = self.convert_markdown_to_pdf(md_path, pdf_file)
        
        if success:
            file_size = pdf_file.stat().st_size / 1024  # KB
            print(f"✅ PDF created: {pdf_file} ({file_size:.1f} KB)")
            return pdf_file
        else:
            print(f"❌ Conversion failed for {md_path.name}")
            return False
    
    def batch_convert_content(self, base_dir=None):
        """Convert all relevant markdown files to PDF"""
        if not base_dir:
            base_dir = Path(__file__).parent.parent
        else:
            base_dir = Path(base_dir)
        
        print("🎙️ Converting podcast content to PDF...")
        
        # Find all relevant markdown files
        content_patterns = [
            'content/wsj_filtered/*.md',
            'content/canary_media/*.md', 
            'content/master_transcripts_organized/*.md',
            'podcast_files/master_files/*.md'
        ]
        
        pdf_output_dir = base_dir / 'content' / 'pdf_exports'
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        
        converted_files = []
        
        for pattern in content_patterns:
            files = list(base_dir.glob(pattern))
            if files:
                # Get the directory name for organization
                content_type = Path(pattern).parts[1] if '/' in pattern else 'other'
                type_output_dir = pdf_output_dir / content_type
                
                print(f"\\n📂 Processing {content_type} ({len(files)} files)...")
                
                for md_file in files:
                    pdf_file = self.convert_file(md_file, type_output_dir)
                    if pdf_file:
                        converted_files.append(pdf_file)
        
        # Generate summary
        print(f"\\n✅ Conversion complete! {len(converted_files)} PDFs generated")
        print(f"📁 Output directory: {pdf_output_dir}")
        
        return converted_files


def main():
    parser = argparse.ArgumentParser(description='Simple Markdown to PDF converter')
    parser.add_argument('--file', '-f', help='Convert single markdown file')
    parser.add_argument('--output', '-o', help='Output directory for PDF files')
    parser.add_argument('--batch', '-b', action='store_true', 
                       help='Batch convert all podcast content')
    parser.add_argument('--install', action='store_true', 
                       help='Install required dependencies')
    parser.add_argument('--name', '-n', help='Custom name for PDF file (single file mode)')
    
    args = parser.parse_args()
    
    converter = SimpleMarkdownToPDF()
    
    # Install dependencies if requested
    if args.install:
        if converter.install_dependencies():
            converter.reportlab_available = True
        else:
            return 1
    
    # Check if reportlab is available
    if not converter.reportlab_available:
        print("❌ Reportlab not available!")
        print("Run with --install to install the required dependency.")
        return 1
    
    # Perform conversions
    if args.batch:
        converted_files = converter.batch_convert_content()
        print(f"🎉 Batch conversion complete! {len(converted_files)} PDFs generated.")
        
    elif args.file:
        pdf_file = converter.convert_file(args.file, args.output, args.name)
        if pdf_file:
            print(f"🎉 Conversion complete!")
        else:
            return 1
            
    else:
        print("📋 Simple Markdown to PDF Converter")
        print("Usage examples:")
        print("  python simple_md_to_pdf.py --batch                           # Convert all content")
        print("  python simple_md_to_pdf.py --file report.md                  # Convert single file")
        print("  python simple_md_to_pdf.py --install                         # Install dependencies")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())