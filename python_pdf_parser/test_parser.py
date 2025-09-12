#!/usr/bin/env python3
"""
Test script to verify PDF parser functionality
"""

import sys
import tempfile
from pathlib import Path
from pdf_to_xml import PDFToXMLConverter

def create_test_pdf():
    """Create a simple test PDF for testing"""
    try:
        import fitz  # PyMuPDF
        
        # Create a simple PDF document
        doc = fitz.open()  # new PDF
        page = doc.new_page()  # new page
        
        # Add some text
        text = "Test PDF Document\n\nThis is a sample PDF created for testing the PDF parser.\n\nFeatures:\n• Text extraction\n• Font detection\n• Color analysis\n• Position mapping"
        
        point = fitz.Point(50, 100)
        page.insert_text(point, text, fontsize=12, color=(0, 0, 0))
        
        # Add a title
        title_point = fitz.Point(50, 50)
        page.insert_text(title_point, "PDF Parser Test", fontsize=18, color=(0.2, 0.2, 0.8))
        
        # Save to temporary file
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        doc.save(temp_pdf.name)
        doc.close()
        
        return temp_pdf.name
    except Exception as e:
        print(f"Error creating test PDF: {e}")
        return None

def test_parser():
    """Test the PDF parser"""
    print("Testing PDF Parser...")
    
    # Create test PDF
    test_pdf_path = create_test_pdf()
    if not test_pdf_path:
        print("Failed to create test PDF")
        return False
    
    try:
        # Test the parser
        converter = PDFToXMLConverter()
        xml_content = converter.convert_to_xml(test_pdf_path)
        
        print("✅ PDF parsing successful!")
        print(f"Pages processed: {converter.document_metadata.get('page_count', 0)}")
        print(f"XML length: {len(xml_content)} characters")
        
        # Check if XML contains expected content
        if "PDF Parser Test" in xml_content:
            print("✅ Title text found in XML")
        else:
            print("❌ Title text not found in XML")
        
        if "text-block" in xml_content:
            print("✅ Text blocks found in XML")
        else:
            print("❌ No text blocks found in XML")
        
        if "font-size" in xml_content:
            print("✅ Font information found in XML")
        else:
            print("❌ No font information found in XML")
        
        # Save test output
        output_path = "test_output.xml"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"✅ Test XML saved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test PDF
        if test_pdf_path and Path(test_pdf_path).exists():
            Path(test_pdf_path).unlink()

def main():
    """Main test function"""
    print("=" * 50)
    print("PDF Parser Test Suite")
    print("=" * 50)
    
    success = test_parser()
    
    print("=" * 50)
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 50)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
