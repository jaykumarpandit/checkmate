#!/usr/bin/env python3
"""
API Wrapper for PDF to XML conversion
Can be called from Node.js or used standalone
"""

import sys
import json
import tempfile
import os
from pathlib import Path
from pdf_to_xml import PDFToXMLConverter

def process_pdf_from_stdin():
    """Process PDF from stdin (for Node.js integration)"""
    try:
        # Read binary data from stdin
        pdf_data = sys.stdin.buffer.read()
        
        if not pdf_data:
            return {"error": "No PDF data received"}
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(pdf_data)
            temp_pdf_path = temp_pdf.name
        
        try:
            # Convert PDF to XML
            converter = PDFToXMLConverter()
            xml_content = converter.convert_to_xml(temp_pdf_path)
            
            return {
                "success": True,
                "xml_content": xml_content,
                "metadata": converter.document_metadata,
                "extraction_method": "pdfminer.six + PyMuPDF"
            }
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
    
    except Exception as e:
        return {
            "error": str(e),
            "extraction_method": "failed"
        }

def process_pdf_file(file_path: str):
    """Process PDF from file path"""
    try:
        if not Path(file_path).exists():
            return {"error": f"File not found: {file_path}"}
        
        converter = PDFToXMLConverter()
        xml_content = converter.convert_to_xml(file_path)
        
        return {
            "success": True,
            "xml_content": xml_content,
            "metadata": converter.document_metadata,
            "extraction_method": "pdfminer.six + PyMuPDF"
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "extraction_method": "failed"
        }

def main():
    """Main function"""
    if len(sys.argv) == 1:
        # No arguments - read from stdin
        result = process_pdf_from_stdin()
    elif len(sys.argv) == 2:
        # File path provided
        result = process_pdf_file(sys.argv[1])
    else:
        result = {"error": "Usage: python api_wrapper.py [pdf_file_path]"}
    
    # Output JSON result
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
