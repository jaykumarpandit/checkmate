#!/usr/bin/env python3
"""
XML to PDF Converter
Converts our custom XML structure back to PDF format using ReportLab
"""

import sys
import json
import tempfile
import base64
from pathlib import Path
from typing import Dict, List, Any
import xml.etree.ElementTree as ET
from io import BytesIO

# PDF creation imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import Color, black, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import tt2ps
from PIL import Image

class XMLToPDFConverter:
    def __init__(self):
        self.page_width = 595  # Default A4 width in points
        self.page_height = 842  # Default A4 height in points
        
    def parse_color(self, color_str: str) -> Color:
        """Parse color string to ReportLab Color object"""
        try:
            if color_str.startswith('#') and len(color_str) == 7:
                r = int(color_str[1:3], 16) / 255.0
                g = int(color_str[3:5], 16) / 255.0
                b = int(color_str[5:7], 16) / 255.0
                return Color(r, g, b)
            return black
        except:
            return black
    
    def get_font_name(self, font_family: str, font_weight: str, font_style: str) -> str:
        """Map font family/weight/style to ReportLab font name"""
        font_family = font_family.lower()
        
        # Standard fonts mapping
        if 'helvetica' in font_family or 'arial' in font_family:
            if font_weight == 'bold' and font_style == 'italic':
                return 'Helvetica-BoldOblique'
            elif font_weight == 'bold':
                return 'Helvetica-Bold'
            elif font_style == 'italic':
                return 'Helvetica-Oblique'
            else:
                return 'Helvetica'
        elif 'times' in font_family:
            if font_weight == 'bold' and font_style == 'italic':
                return 'Times-BoldItalic'
            elif font_weight == 'bold':
                return 'Times-Bold'
            elif font_style == 'italic':
                return 'Times-Italic'
            else:
                return 'Times-Roman'
        elif 'courier' in font_family:
            if font_weight == 'bold' and font_style == 'italic':
                return 'Courier-BoldOblique'
            elif font_weight == 'bold':
                return 'Courier-Bold'
            elif font_style == 'italic':
                return 'Courier-Oblique'
            else:
                return 'Courier'
        else:
            # Default to Helvetica
            return 'Helvetica'
    
    def convert_coordinates(self, x: float, y: float, page_height: float, text_height: float = 0) -> tuple:
        """Convert PDF coordinates to ReportLab coordinates"""
        # PDF coordinates: origin at bottom-left
        # Our XML coordinates: origin at top-left  
        # For proper text positioning, we need to account for the baseline
        new_y = page_height - y - text_height
        return (x, new_y)
    
    def draw_text_block(self, canvas_obj, block: Dict[str, Any], page_height: float):
        """Draw a text block on the canvas"""
        try:
            text = block.get('text', '')
            if not text.strip():
                return
            
            x = float(block.get('x', 0))
            y = float(block.get('y', 0))
            font_size = float(block.get('font-size', 12))
            font_family = block.get('font-family', 'Helvetica')
            font_weight = block.get('font-weight', 'normal')
            font_style = block.get('font-style', 'normal')
            color_str = block.get('color', '#000000')
            
            # Convert coordinates with proper text height adjustment
            canvas_x, canvas_y = self.convert_coordinates(x, y, page_height, font_size)
            
            # Set font
            font_name = self.get_font_name(font_family, font_weight, font_style)
            canvas_obj.setFont(font_name, font_size)
            
            # Set color
            color = self.parse_color(color_str)
            canvas_obj.setFillColor(color)
            
            # Draw text with proper baseline alignment
            canvas_obj.drawString(canvas_x, canvas_y, text)
            
        except Exception as e:
            print(f"Error drawing text block: {e}", file=sys.stderr)
    
    def draw_image(self, canvas_obj, image_data: Dict[str, Any], page_height: float):
        """Draw an image on the canvas"""
        try:
            x = float(image_data.get('x', 0))
            y = float(image_data.get('y', 0))
            width = float(image_data.get('width', 100))
            height = float(image_data.get('height', 100))
            encoding = image_data.get('encoding', '')
            data = image_data.get('data', '')
            
            if encoding == 'base64' and data:
                # Convert coordinates
                canvas_x, canvas_y = self.convert_coordinates(x, y + height, page_height)
                
                # Decode base64 image
                image_bytes = base64.b64decode(data)
                image_io = BytesIO(image_bytes)
                
                # Create PIL Image
                pil_image = Image.open(image_io)
                
                # Draw image
                canvas_obj.drawInlineImage(pil_image, canvas_x, canvas_y, width, height)
                
        except Exception as e:
            print(f"Error drawing image: {e}", file=sys.stderr)
    
    def draw_line(self, canvas_obj, line_data: Dict[str, Any], page_height: float):
        """Draw a line on the canvas"""
        try:
            x1 = float(line_data.get('x1', 0))
            y1 = float(line_data.get('y1', 0))
            x2 = float(line_data.get('x2', 0))
            y2 = float(line_data.get('y2', 0))
            color_str = line_data.get('color', '#000000')
            line_width = float(line_data.get('width', 1))
            
            # Convert coordinates
            canvas_x1, canvas_y1 = self.convert_coordinates(x1, y1, page_height)
            canvas_x2, canvas_y2 = self.convert_coordinates(x2, y2, page_height)
            
            # Set line properties
            color = self.parse_color(color_str)
            canvas_obj.setStrokeColor(color)
            canvas_obj.setLineWidth(line_width)
            
            # Draw line
            canvas_obj.line(canvas_x1, canvas_y1, canvas_x2, canvas_y2)
            
        except Exception as e:
            print(f"Error drawing line: {e}", file=sys.stderr)
    
    def draw_rectangle(self, canvas_obj, rect_data: Dict[str, Any], page_height: float):
        """Draw a rectangle on the canvas"""
        try:
            x = float(rect_data.get('x', 0))
            y = float(rect_data.get('y', 0))
            width = float(rect_data.get('width', 100))
            height = float(rect_data.get('height', 100))
            color_str = rect_data.get('color', '#000000')
            fill = rect_data.get('fill', 'none')
            
            # Convert coordinates
            canvas_x, canvas_y = self.convert_coordinates(x, y + height, page_height)
            
            # Set properties
            color = self.parse_color(color_str)
            canvas_obj.setStrokeColor(color)
            
            if fill != 'none':
                canvas_obj.setFillColor(color)
                canvas_obj.rect(canvas_x, canvas_y, width, height, fill=1)
            else:
                canvas_obj.rect(canvas_x, canvas_y, width, height, fill=0)
                
        except Exception as e:
            print(f"Error drawing rectangle: {e}", file=sys.stderr)
    
    def convert_xml_to_pdf(self, xml_content: str, output_path: str) -> bool:
        """Convert XML content to PDF file"""
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Get metadata
            metadata = {}
            metadata_elem = root.find('metadata')
            if metadata_elem is not None:
                for child in metadata_elem:
                    metadata[child.tag] = child.text or ''
            
            # Create PDF
            c = canvas.Canvas(output_path, pagesize=A4)
            
            # Set metadata
            if metadata.get('title'):
                c.setTitle(metadata['title'])
            if metadata.get('author'):
                c.setAuthor(metadata['author'])
            if metadata.get('creator'):
                c.setCreator(metadata['creator'])
            if metadata.get('subject'):
                c.setSubject(metadata['subject'])
            
            # Process pages
            pages = root.find('pages')
            if pages is not None:
                for page_elem in pages.findall('page'):
                    page_num = int(page_elem.get('number', 1))
                    page_width = float(page_elem.get('width', 595))
                    page_height = float(page_elem.get('height', 842))
                    
                    print(f"Processing page {page_num} ({page_width}x{page_height})", file=sys.stderr)
                    
                    # Set page size
                    c.setPageSize((page_width, page_height))
                    
                    # Draw text blocks
                    text_blocks = page_elem.find('text-blocks')
                    if text_blocks is not None:
                        for text_block in text_blocks.findall('text-block'):
                            block_data = {
                                'text': text_block.text or '',
                                'x': text_block.get('x', '0'),
                                'y': text_block.get('y', '0'),
                                'font-size': text_block.get('font-size', '12'),
                                'font-family': text_block.get('font-family', 'Helvetica'),
                                'font-weight': text_block.get('font-weight', 'normal'),
                                'font-style': text_block.get('font-style', 'normal'),
                                'color': text_block.get('color', '#000000')
                            }
                            self.draw_text_block(c, block_data, page_height)
                    
                    # Draw images
                    images = page_elem.find('images')
                    if images is not None:
                        for image in images.findall('image'):
                            image_data = {
                                'x': image.get('x', '0'),
                                'y': image.get('y', '0'),
                                'width': image.get('width', '100'),
                                'height': image.get('height', '100'),
                                'encoding': image.get('encoding', ''),
                                'data': image.text or ''
                            }
                            self.draw_image(c, image_data, page_height)
                    
                    # Draw shapes
                    shapes = page_elem.find('shapes')
                    if shapes is not None:
                        for line in shapes.findall('line'):
                            line_data = {
                                'x1': line.get('x1', '0'),
                                'y1': line.get('y1', '0'),
                                'x2': line.get('x2', '0'),
                                'y2': line.get('y2', '0'),
                                'color': line.get('color', '#000000'),
                                'width': line.get('width', '1')
                            }
                            self.draw_line(c, line_data, page_height)
                        
                        for rect in shapes.findall('rectangle'):
                            rect_data = {
                                'x': rect.get('x', '0'),
                                'y': rect.get('y', '0'),
                                'width': rect.get('width', '100'),
                                'height': rect.get('height', '100'),
                                'color': rect.get('color', '#000000'),
                                'fill': rect.get('fill', 'none')
                            }
                            self.draw_rectangle(c, rect_data, page_height)
                    
                    # Finish page
                    c.showPage()
            
            # Save PDF
            c.save()
            print(f"PDF successfully created: {output_path}", file=sys.stderr)
            return True
            
        except Exception as e:
            print(f"Error converting XML to PDF: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return False

def main():
    """Main function for command line usage"""
    if len(sys.argv) != 3:
        print("Usage: python xml_to_pdf.py <input_xml> <output_pdf>")
        sys.exit(1)
    
    input_xml = sys.argv[1]
    output_pdf = sys.argv[2]
    
    if not Path(input_xml).exists():
        print(f"Error: Input XML file '{input_xml}' not found")
        sys.exit(1)
    
    try:
        with open(input_xml, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        converter = XMLToPDFConverter()
        success = converter.convert_xml_to_pdf(xml_content, output_pdf)
        
        if success:
            print(f"Successfully converted '{input_xml}' to '{output_pdf}'")
        else:
            print("Conversion failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
