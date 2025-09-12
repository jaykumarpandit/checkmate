#!/usr/bin/env python3
"""
API Wrapper for XML to PDF conversion
Can be called from Node.js with JSON input
"""

import sys
import json
import tempfile
import os
from pathlib import Path
from xml_to_pdf import XMLToPDFConverter

def process_xml_to_pdf_from_stdin():
    """Process XML to PDF conversion from stdin (for Node.js integration)"""
    try:
        # Read JSON data from stdin
        input_data = sys.stdin.read()
        
        if not input_data:
            return {"error": "No data received"}
        
        # Parse JSON
        data = json.loads(input_data)
        xml_content = data.get('xmlContent', '')
        filename = data.get('fileName', 'converted.pdf')
        
        if not xml_content:
            return {"error": "No XML content provided"}
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        try:
            # Convert XML to PDF
            converter = XMLToPDFConverter()
            success = converter.convert_xml_to_pdf(xml_content, temp_pdf_path)
            
            if not success:
                return {"error": "XML to PDF conversion failed"}
            
            # Read the generated PDF
            with open(temp_pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            # Return binary data as base64
            import base64
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            return {
                "success": True,
                "pdf_data": pdf_base64,
                "filename": filename,
                "size": len(pdf_data),
                "conversion_method": "ReportLab"
            }
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
    
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON input: {str(e)}"}
    except Exception as e:
        return {"error": f"Conversion error: {str(e)}"}

def process_xml_file_to_pdf(xml_file: str, output_file: str):
    """Process XML file to PDF file"""
    try:
        if not Path(xml_file).exists():
            return {"error": f"XML file not found: {xml_file}"}
        
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        converter = XMLToPDFConverter()
        success = converter.convert_xml_to_pdf(xml_content, output_file)
        
        if success:
            file_size = Path(output_file).stat().st_size if Path(output_file).exists() else 0
            return {
                "success": True,
                "output_file": output_file,
                "size": file_size,
                "conversion_method": "ReportLab"
            }
        else:
            return {"error": "XML to PDF conversion failed"}
    
    except Exception as e:
        return {"error": f"Conversion error: {str(e)}"}

def main():
    """Main function"""
    if len(sys.argv) == 1:
        # No arguments - read JSON from stdin
        result = process_xml_to_pdf_from_stdin()
    elif len(sys.argv) == 3:
        # Two arguments - XML file and output PDF file
        result = process_xml_file_to_pdf(sys.argv[1], sys.argv[2])
    else:
        result = {"error": "Usage: python xml_to_pdf_api.py [xml_file output_pdf] or pipe JSON to stdin"}
    
    # Output JSON result
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
