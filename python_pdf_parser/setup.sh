#!/bin/bash

# Setup script for Python PDF parser
echo "Setting up Python PDF parser..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete!"
echo ""
echo "To use the PDF parser:"
echo "1. Activate the virtual environment: source python_pdf_parser/venv/bin/activate"
echo "2. Run: python python_pdf_parser/pdf_to_xml.py input.pdf output.xml"
echo "3. Or use API wrapper: python python_pdf_parser/api_wrapper.py input.pdf"
