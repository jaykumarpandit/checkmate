#!/usr/bin/env python3
"""
PDF to XML Converter using pdfminer.six
Extracts text, images, fonts, colors, and positioning information
"""

import sys
import io
import base64
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom

# PDF processing imports
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTImage, LTFigure, LTRect, LTLine
from pdfminer.layout import LAParams, LTTextLine, LTTextBox
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTPage
from pdfminer.pdfpage import PDFDocument, PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter

# For image extraction
import fitz  # PyMuPDF for better image extraction

class PDFToXMLConverter:
    def __init__(self):
        self.pages_data = []
        self.document_metadata = {}
        
    def extract_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """Extract basic PDF metadata"""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            self.document_metadata = {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'page_count': doc.page_count
            }
            doc.close()
            return self.document_metadata
        except Exception as e:
            print(f"Error extracting PDF metadata: {e}")
            return {}
    
    def extract_images_from_page(self, pdf_path: str, page_num: int) -> List[Dict[str, Any]]:
        """Extract images from a specific page using PyMuPDF"""
        images = []
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.pil_tobytes(format="PNG")
                        img_base64 = base64.b64encode(img_data).decode()
                        
                        # Get image position and size
                        img_rect = page.get_image_bbox(img)
                        
                        images.append({
                            'id': f'image-{page_num + 1}-{img_index + 1}',
                            'x': round(img_rect.x0, 2),
                            'y': round(img_rect.y0, 2),
                            'width': round(img_rect.width, 2),
                            'height': round(img_rect.height, 2),
                            'rotation': 0,
                            'encoding': 'base64',
                            'data': img_base64,
                            'format': 'PNG'
                        })
                    
                    pix = None
                except Exception as e:
                    print(f"Error processing image {img_index}: {e}")
                    continue
            
            doc.close()
            return images
        except Exception as e:
            print(f"Error extracting images from page {page_num}: {e}")
            return []
    
    def analyze_char_properties(self, char: LTChar) -> Dict[str, Any]:
        """Extract detailed character properties"""
        return {
            'font_name': char.fontname,
            'font_size': round(char.height, 2),
            'color': self.get_char_color(char),
            'x': round(char.x0, 2),
            'y': round(char.y0, 2),
            'width': round(char.width, 2),
            'height': round(char.height, 2),
            'text': char.get_text()
        }
    
    def get_char_color(self, char: LTChar) -> str:
        """Extract color information from character"""
        try:
            # Try multiple methods to get color information
            color = None
            
            # Method 1: From graphicstate ncolor
            if hasattr(char, 'graphicstate') and char.graphicstate:
                if hasattr(char.graphicstate, 'ncolor') and char.graphicstate.ncolor:
                    color = char.graphicstate.ncolor
                # Method 2: From graphicstate scolor (stroke color)
                elif hasattr(char.graphicstate, 'scolor') and char.graphicstate.scolor:
                    color = char.graphicstate.scolor
            
            # Method 3: Check if color info is in textstate
            if not color and hasattr(char, 'textstate') and char.textstate:
                if hasattr(char.textstate, 'ncolor') and char.textstate.ncolor:
                    color = char.textstate.ncolor
            
            # Method 4: Try to get from font color attributes
            if not color and hasattr(char, '_font_color'):
                color = char._font_color
            
            if color:
                # Convert to hex color
                if isinstance(color, (list, tuple)) and len(color) >= 3:
                    r = int(color[0] * 255) if color[0] <= 1 else int(color[0])
                    g = int(color[1] * 255) if color[1] <= 1 else int(color[1])
                    b = int(color[2] * 255) if color[2] <= 1 else int(color[2])
                    return f"#{r:02x}{g:02x}{b:02x}"
                elif isinstance(color, (int, float)):
                    # Grayscale color
                    gray = int(color * 255) if color <= 1 else int(color)
                    return f"#{gray:02x}{gray:02x}{gray:02x}"
            
            return "#000000"  # Default black
        except Exception as e:
            print(f"Color extraction error: {e}", file=sys.stderr)
            return "#000000"
    
    def group_chars_into_text_blocks(self, chars: List[Dict]) -> List[Dict[str, Any]]:
        """Group characters into logical text blocks with proper coordinate handling"""
        if not chars:
            return []
        
        # Filter out characters that look like filler text
        filtered_chars = []
        for char in chars:
            text = char['text'].strip()
            # Skip empty chars and obvious filler patterns
            if (text and 
                not text.isspace() and 
                len(text) > 0 and
                # Filter out repetitive filler text patterns
                not (len(text) > 3 and text.lower().count('and more') > 0 and len(text) < 20)):
                filtered_chars.append(char)
        
        if not filtered_chars:
            return []
        
        # Group characters by lines first (same y-coordinate)
        lines = {}
        for char in filtered_chars:
            y_key = round(char['y'], 1)  # Round to handle small variations
            if y_key not in lines:
                lines[y_key] = []
            lines[y_key].append(char)
        
        # Sort lines by y-coordinate (top to bottom)
        sorted_lines = sorted(lines.items(), key=lambda x: -x[0])  # Negative for top-to-bottom
        
        text_blocks = []
        
        for y_coord, line_chars in sorted_lines:
            # Sort characters in this line by x-coordinate (left to right)
            line_chars.sort(key=lambda c: c['x'])
            
            # Group characters in this line into text blocks
            if not line_chars:
                continue
                
            current_block = {
                'chars': [line_chars[0]],
                'text': line_chars[0]['text'],
                'x': line_chars[0]['x'],
                'y': line_chars[0]['y'],
                'font_name': line_chars[0]['font_name'],
                'font_size': line_chars[0]['font_size'],
                'color': line_chars[0]['color']
            }
            
            for char in line_chars[1:]:
                # Calculate x distance
                x_diff = char['x'] - (current_block['x'] + sum(c['width'] for c in current_block['chars']))
                
                # Check if this character continues the current block
                reasonable_gap = (x_diff < current_block['font_size'] * 2)  # Word spacing
                same_color = (char['color'] == current_block['color'])
                similar_font = (char['font_name'] == current_block['font_name'] and 
                              abs(char['font_size'] - current_block['font_size']) < 2)
                
                if reasonable_gap and same_color and similar_font:
                    # Add space if there's a gap
                    if x_diff > current_block['font_size'] * 0.2:
                        current_block['text'] += ' '
                    current_block['chars'].append(char)
                    current_block['text'] += char['text']
                else:
                    # Finalize current block and start new one
                    if current_block['text'].strip() and len(current_block['text'].strip()) > 1:
                        text_blocks.append(self.finalize_text_block(current_block))
                    
                    current_block = {
                        'chars': [char],
                        'text': char['text'],
                        'x': char['x'],
                        'y': char['y'],
                        'font_name': char['font_name'],
                        'font_size': char['font_size'],
                        'color': char['color']
                    }
            
            # Add the last block of this line
            if current_block['text'].strip() and len(current_block['text'].strip()) > 1:
                text_blocks.append(self.finalize_text_block(current_block))
        
        return text_blocks
    
    def finalize_text_block(self, block: Dict) -> Dict[str, Any]:
        """Finalize a text block with calculated properties"""
        chars = block['chars']
        min_x = min(c['x'] for c in chars)
        max_x = max(c['x'] + c['width'] for c in chars)
        min_y = min(c['y'] for c in chars)
        max_y = max(c['y'] + c['height'] for c in chars)
        
        # Use the most common font size in the block
        font_sizes = [c['font_size'] for c in chars]
        most_common_size = max(set(font_sizes), key=font_sizes.count)
        
        # Use the color from the first character (or most common)
        colors = [c['color'] for c in chars]
        most_common_color = max(set(colors), key=colors.count)
        
        # Determine text properties from font name
        font_name = block['font_name'].lower()
        font_weight = 'bold' if any(w in font_name for w in ['bold', 'black', 'heavy']) else 'normal'
        font_style = 'italic' if any(s in font_name for s in ['italic', 'oblique']) else 'normal'
        
        # Clean font name - handle various font name formats
        font_family = block['font_name']
        if '+' in font_family:
            font_family = font_family.split('+')[-1]
        if '-' in font_family:
            base_name = font_family.split('-')[0]
            if base_name:
                font_family = base_name
        
        # Map common font names
        font_family_map = {
            'times': 'Times-Roman',
            'helvetica': 'Helvetica',
            'arial': 'Arial', 
            'courier': 'Courier'
        }
        
        for key, value in font_family_map.items():
            if key in font_family.lower():
                font_family = value
                break
        
        if not font_family or len(font_family) < 2:
            font_family = 'Helvetica'
        
        # Clean up the text and check for filler content
        final_text = block['text'].strip()
        
        # Additional filtering for repetitive content
        if (final_text.lower().count('and more text') > 2 or 
            final_text.lower().count('more text') > 3 or
            (len(final_text) > 50 and final_text.lower().count('and more') > 3)):
            # This looks like filler text, try to extract meaningful parts
            words = final_text.split()
            meaningful_words = []
            for word in words:
                if word.lower() not in ['and', 'more', 'text', 'text.']:
                    meaningful_words.append(word)
                elif len(meaningful_words) > 0:  # Keep some context
                    meaningful_words.append(word)
                if len(meaningful_words) > 20:  # Limit length
                    break
            final_text = ' '.join(meaningful_words) if meaningful_words else final_text
        
        return {
            'text': final_text,
            'x': round(min_x, 2),
            'y': round(min_y, 2),
            'width': round(max_x - min_x, 2),
            'height': round(max_y - min_y, 2),
            'font_size': round(most_common_size, 1),
            'font_family': font_family,
            'font_weight': font_weight,
            'font_style': font_style,
            'color': most_common_color,
            'rotation': 0,
            'direction': 'ltr'
        }
    
    def extract_lines_and_shapes(self, page_layout) -> List[Dict[str, Any]]:
        """Extract lines and geometric shapes from the page"""
        shapes = []
        
        def process_element(element):
            if isinstance(element, LTLine):
                shapes.append({
                    'type': 'line',
                    'x1': round(element.x0, 2),
                    'y1': round(element.y0, 2),
                    'x2': round(element.x1, 2),
                    'y2': round(element.y1, 2),
                    'color': '#000000',  # Default color
                    'width': round(getattr(element, 'linewidth', 1), 2)
                })
            elif isinstance(element, LTRect):
                shapes.append({
                    'type': 'rectangle',
                    'x': round(element.x0, 2),
                    'y': round(element.y0, 2),
                    'width': round(element.width, 2),
                    'height': round(element.height, 2),
                    'color': '#000000',
                    'fill': 'none'
                })
            elif hasattr(element, '__iter__'):
                for child in element:
                    process_element(child)
        
        process_element(page_layout)
        return shapes
    
    def process_pdf_page(self, page_layout, page_num: int, pdf_path: str) -> Dict[str, Any]:
        """Process a single PDF page and extract all elements"""
        
        # Primary extraction using PyMuPDF for better accuracy
        try:
            import fitz
            doc = fitz.open(pdf_path)
            fitz_page = doc[page_num]
            
            # Get clean text from PyMuPDF
            pymupdf_text = fitz_page.get_text()
            print(f"PyMuPDF extracted text preview: {pymupdf_text[:200]}...", file=sys.stderr)
            
            # Extract text blocks with positioning and styling from PyMuPDF
            text_blocks = []
            blocks = fitz_page.get_text("dict")
            
            if blocks and 'blocks' in blocks:
                for block_idx, block in enumerate(blocks['blocks']):
                    if 'lines' in block:
                        for line_idx, line in enumerate(block['lines']):
                            if 'spans' in line:
                                for span_idx, span in enumerate(line['spans']):
                                    span_text = span.get('text', '').strip()
                                    
                                    # Skip empty or filler text
                                    if (not span_text or 
                                        span_text.isspace() or
                                        (span_text.lower().count('and more') > 1 and len(span_text) < 30)):
                                        continue
                                    
                                    bbox = span['bbox']
                                    font_info = span.get('font', 'Helvetica')
                                    font_size = span.get('size', 12)
                                    
                                    # Extract color
                                    color_int = span.get('color', 0)
                                    r = (color_int >> 16) & 255
                                    g = (color_int >> 8) & 255
                                    b = color_int & 255
                                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                                    
                                    # Determine font properties
                                    font_name = font_info.lower()
                                    font_weight = 'bold' if any(w in font_name for w in ['bold', 'black']) else 'normal'
                                    font_style = 'italic' if any(s in font_name for s in ['italic', 'oblique']) else 'normal'
                                    
                                    # Clean font family name
                                    font_family = font_info
                                    if '+' in font_family:
                                        font_family = font_family.split('+')[-1]
                                    if '-' in font_family:
                                        font_family = font_family.split('-')[0]
                                    
                                    text_blocks.append({
                                        'text': span_text,
                                        'x': round(bbox[0], 2),
                                        'y': round(bbox[1], 2),  # PyMuPDF uses bottom-left origin
                                        'width': round(bbox[2] - bbox[0], 2),
                                        'height': round(bbox[3] - bbox[1], 2),
                                        'font_size': round(font_size, 1),
                                        'font_family': font_family,
                                        'font_weight': font_weight,
                                        'font_style': font_style,
                                        'color': hex_color,
                                        'rotation': 0,
                                        'direction': 'ltr'
                                    })
            
            # Sort text blocks by y-coordinate (top to bottom) then x-coordinate (left to right)
            text_blocks.sort(key=lambda b: (-b['y'], b['x']))
            
            # Extract images
            images = self.extract_images_from_page(pdf_path, page_num)
            
            # Extract shapes and lines from pdfminer
            shapes = self.extract_lines_and_shapes(page_layout)
            
            doc.close()
            
            return {
                'page_number': page_num + 1,
                'width': round(page_layout.width, 2),
                'height': round(page_layout.height, 2),
                'text_blocks': text_blocks,
                'images': images,
                'shapes': shapes,
                'char_count': len(text_blocks),  # Using blocks as char count approximation
                'text_length': sum(len(block['text']) for block in text_blocks)
            }
            
        except Exception as e:
            print(f"PyMuPDF extraction failed, falling back to pdfminer: {e}", file=sys.stderr)
            
            # Fallback to original pdfminer extraction
            page_chars = []
            
            def extract_chars(element):
                if isinstance(element, LTChar):
                    char_info = self.analyze_char_properties(element)
                    page_chars.append(char_info)
                elif hasattr(element, '__iter__'):
                    for child in element:
                        extract_chars(child)
            
            # Extract all characters
            extract_chars(page_layout)
            
            # Group characters into text blocks
            text_blocks = self.group_chars_into_text_blocks(page_chars)
            
            # Extract images
            images = self.extract_images_from_page(pdf_path, page_num)
            
            # Extract shapes and lines
            shapes = self.extract_lines_and_shapes(page_layout)
            
            return {
                'page_number': page_num + 1,
                'width': round(page_layout.width, 2),
                'height': round(page_layout.height, 2),
                'text_blocks': text_blocks,
                'images': images,
                'shapes': shapes,
                'char_count': len(page_chars),
                'text_length': sum(len(block['text']) for block in text_blocks)
            }
    
    def convert_to_xml(self, pdf_path: str) -> str:
        """Convert PDF to XML format"""
        # Extract metadata
        self.extract_pdf_info(pdf_path)
        
        # Create root XML element
        root = ET.Element('pdf-document')
        
        # Add metadata
        metadata = ET.SubElement(root, 'metadata')
        ET.SubElement(metadata, 'title').text = self.document_metadata.get('title', '')
        ET.SubElement(metadata, 'author').text = self.document_metadata.get('author', '')
        ET.SubElement(metadata, 'subject').text = self.document_metadata.get('subject', '')
        ET.SubElement(metadata, 'creator').text = self.document_metadata.get('creator', '')
        ET.SubElement(metadata, 'producer').text = self.document_metadata.get('producer', '')
        ET.SubElement(metadata, 'creation-date').text = self.document_metadata.get('creation_date', '')
        ET.SubElement(metadata, 'modification-date').text = self.document_metadata.get('modification_date', '')
        ET.SubElement(metadata, 'page-count').text = str(self.document_metadata.get('page_count', 0))
        
        # Add pages
        pages_element = ET.SubElement(root, 'pages')
        
        # Process each page
        laparams = LAParams(
            boxes_flow=0.5,
            word_margin=0.1,
            char_margin=2.0,
            line_margin=0.5,
            detect_vertical=True
        )
        
        for page_num, page_layout in enumerate(extract_pages(pdf_path, laparams=laparams)):
            page_data = self.process_pdf_page(page_layout, page_num, pdf_path)
            
            # Create page element
            page_elem = ET.SubElement(pages_element, 'page')
            page_elem.set('number', str(page_data['page_number']))
            page_elem.set('width', str(page_data['width']))
            page_elem.set('height', str(page_data['height']))
            page_elem.set('extraction-method', 'pdfminer.six')
            page_elem.set('char-count', str(page_data['char_count']))
            page_elem.set('text-length', str(page_data['text_length']))
            
            # Add page info
            page_info = ET.SubElement(page_elem, 'page-info')
            dimensions = ET.SubElement(page_info, 'dimensions')
            dimensions.set('width', str(page_data['width']))
            dimensions.set('height', str(page_data['height']))
            
            stats = ET.SubElement(page_info, 'content-stats')
            stats.set('text-blocks', str(len(page_data['text_blocks'])))
            stats.set('images', str(len(page_data['images'])))
            stats.set('shapes', str(len(page_data['shapes'])))
            stats.set('characters', str(page_data['char_count']))
            
            # Add text blocks
            text_blocks_elem = ET.SubElement(page_elem, 'text-blocks')
            text_blocks_elem.set('count', str(len(page_data['text_blocks'])))
            
            for i, block in enumerate(page_data['text_blocks']):
                block_elem = ET.SubElement(text_blocks_elem, 'text-block')
                block_elem.set('id', f"block-{page_data['page_number']}-{i + 1}")
                block_elem.set('x', str(block['x']))
                block_elem.set('y', str(block['y']))
                block_elem.set('width', str(block['width']))
                block_elem.set('height', str(block['height']))
                block_elem.set('font-size', str(block['font_size']))
                block_elem.set('font-family', block['font_family'])
                block_elem.set('font-weight', block['font_weight'])
                block_elem.set('font-style', block['font_style'])
                block_elem.set('color', block['color'])
                block_elem.set('rotation', str(block['rotation']))
                block_elem.set('direction', block['direction'])
                block_elem.text = block['text']
            
            # Add images
            images_elem = ET.SubElement(page_elem, 'images')
            images_elem.set('count', str(len(page_data['images'])))
            
            for image in page_data['images']:
                img_elem = ET.SubElement(images_elem, 'image')
                img_elem.set('id', image['id'])
                img_elem.set('x', str(image['x']))
                img_elem.set('y', str(image['y']))
                img_elem.set('width', str(image['width']))
                img_elem.set('height', str(image['height']))
                img_elem.set('rotation', str(image['rotation']))
                img_elem.set('encoding', image['encoding'])
                img_elem.set('format', image['format'])
                img_elem.text = image['data']
            
            # Add shapes and lines
            if page_data['shapes']:
                shapes_elem = ET.SubElement(page_elem, 'shapes')
                shapes_elem.set('count', str(len(page_data['shapes'])))
                
                for j, shape in enumerate(page_data['shapes']):
                    if shape['type'] == 'line':
                        line_elem = ET.SubElement(shapes_elem, 'line')
                        line_elem.set('id', f"line-{page_data['page_number']}-{j + 1}")
                        line_elem.set('x1', str(shape['x1']))
                        line_elem.set('y1', str(shape['y1']))
                        line_elem.set('x2', str(shape['x2']))
                        line_elem.set('y2', str(shape['y2']))
                        line_elem.set('color', shape['color'])
                        line_elem.set('width', str(shape['width']))
                    elif shape['type'] == 'rectangle':
                        rect_elem = ET.SubElement(shapes_elem, 'rectangle')
                        rect_elem.set('id', f"rect-{page_data['page_number']}-{j + 1}")
                        rect_elem.set('x', str(shape['x']))
                        rect_elem.set('y', str(shape['y']))
                        rect_elem.set('width', str(shape['width']))
                        rect_elem.set('height', str(shape['height']))
                        rect_elem.set('color', shape['color'])
                        rect_elem.set('fill', shape['fill'])
        
        # Convert to pretty XML string
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")


def main():
    """Main function to handle command line usage"""
    if len(sys.argv) != 3:
        print("Usage: python pdf_to_xml.py <input_pdf> <output_xml>")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_xml = sys.argv[2]
    
    if not Path(input_pdf).exists():
        print(f"Error: Input PDF file '{input_pdf}' not found")
        sys.exit(1)
    
    try:
        converter = PDFToXMLConverter()
        xml_content = converter.convert_to_xml(input_pdf)
        
        with open(output_xml, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"Successfully converted '{input_pdf}' to '{output_xml}'")
        print(f"Pages processed: {converter.document_metadata.get('page_count', 0)}")
        
    except Exception as e:
        print(f"Error converting PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
