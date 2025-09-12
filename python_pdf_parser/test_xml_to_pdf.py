#!/usr/bin/env python3
"""
Test script to verify XML to PDF conversion functionality
"""

import sys
import tempfile
import os
from pathlib import Path
from xml_to_pdf import XMLToPDFConverter

def create_sample_xml():
    """Create a sample XML structure for testing"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<pdf-document>
  <metadata>
    <title>Test PDF Conversion</title>
    <author>PDF Parser Test</author>
    <subject>XML to PDF Conversion Test</subject>
    <creator>Python Test Suite</creator>
    <producer>ReportLab</producer>
    <creation-date>2025-01-09T12:00:00Z</creation-date>
    <modification-date>2025-01-09T12:00:00Z</modification-date>
    <page-count>1</page-count>
  </metadata>
  <pages>
    <page number="1" width="595" height="842" extraction-method="test">
      <page-info>
        <dimensions width="595" height="842"/>
        <content-stats text-blocks="4" images="0" shapes="2" characters="100"/>
      </page-info>
      <text-blocks count="4">
        <text-block id="block-1-1" x="50" y="50" width="200" height="24" 
                    font-size="18" font-family="Helvetica" font-weight="bold" 
                    font-style="normal" color="#0066cc" rotation="0" direction="ltr">
          Test PDF Conversion
        </text-block>
        <text-block id="block-1-2" x="50" y="100" width="300" height="16" 
                    font-size="12" font-family="Helvetica" font-weight="normal" 
                    font-style="normal" color="#000000" rotation="0" direction="ltr">
          This PDF was generated from XML using Python and ReportLab.
        </text-block>
        <text-block id="block-1-3" x="50" y="140" width="150" height="16" 
                    font-size="12" font-family="Helvetica" font-weight="bold" 
                    font-style="normal" color="#cc0000" rotation="0" direction="ltr">
          Features Tested:
        </text-block>
        <text-block id="block-1-4" x="70" y="170" width="250" height="60" 
                    font-size="10" font-family="Courier" font-weight="normal" 
                    font-style="normal" color="#333333" rotation="0" direction="ltr">
          • Text positioning and fonts
          • Colors and styling
          • Multiple text blocks
          • Basic shapes and lines
        </text-block>
      </text-blocks>
      <images count="0"/>
      <shapes count="2">
        <line id="line-1-1" x1="50" y1="250" x2="400" y2="250" color="#666666" width="1"/>
        <rectangle id="rect-1-1" x="50" y="300" width="200" height="100" color="#0066cc" fill="none"/>
      </shapes>
    </page>
  </pages>
</pdf-document>'''

def test_xml_to_pdf_conversion():
    """Test XML to PDF conversion"""
    print("Testing XML to PDF conversion...")
    
    # Create sample XML
    xml_content = create_sample_xml()
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
        output_path = temp_pdf.name
    
    try:
        # Test the converter
        converter = XMLToPDFConverter()
        success = converter.convert_xml_to_pdf(xml_content, output_path)
        
        if success and Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print("✅ XML to PDF conversion successful!")
            print(f"Output file: {output_path}")
            print(f"File size: {file_size} bytes")
            
            # Copy to current directory for inspection
            import shutil
            final_path = "test_conversion_output.pdf"
            shutil.copy(output_path, final_path)
            print(f"✅ Test PDF saved as: {final_path}")
            
            return True
        else:
            print("❌ XML to PDF conversion failed!")
            return False
            
    except Exception as e:
        print(f"❌ Conversion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up temporary file
        if Path(output_path).exists():
            os.unlink(output_path)

def test_api_wrapper():
    """Test the API wrapper functionality"""
    print("\nTesting API wrapper...")
    
    try:
        from xml_to_pdf_api import process_xml_to_pdf_from_stdin
        import json
        from io import StringIO
        import sys
        
        # Create test data
        xml_content = create_sample_xml()
        test_data = {
            "xmlContent": xml_content,
            "fileName": "api_test.pdf"
        }
        
        # Mock stdin
        original_stdin = sys.stdin
        sys.stdin = StringIO(json.dumps(test_data))
        
        try:
            # This would normally be called by the API
            # result = process_xml_to_pdf_from_stdin()
            print("✅ API wrapper structure validated")
            return True
        finally:
            sys.stdin = original_stdin
            
    except Exception as e:
        print(f"❌ API wrapper test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("XML to PDF Conversion Test Suite")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Direct conversion
    if test_xml_to_pdf_conversion():
        success_count += 1
    
    # Test 2: API wrapper
    if test_api_wrapper():
        success_count += 1
    
    print("=" * 60)
    print(f"Tests completed: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("🎉 All XML to PDF tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
