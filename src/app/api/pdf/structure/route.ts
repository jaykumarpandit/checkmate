import { NextRequest } from "next/server";
import { createPdfXml, type PageData, type TextBlock, type ImageBlock } from "@/lib/pdf/structure";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get("file");
    if (!file || !(file instanceof Blob)) {
      return new Response(JSON.stringify({ error: "Missing file" }), { status: 400 });
    }

    const arrayBuffer = await file.arrayBuffer();
    const fileName = (file as any).name || "document.pdf";
    
    // Use pdf-lib for structure and pdf-parse for text content
    const { PDFDocument } = await import('pdf-lib');
    const pdfDoc = await PDFDocument.load(Buffer.from(arrayBuffer));
    
    // Get metadata from pdf-lib
    const title = pdfDoc.getTitle() || undefined;
    const author = pdfDoc.getAuthor() || undefined;
    const subject = pdfDoc.getSubject() || undefined;
    const creator = pdfDoc.getCreator() || undefined;
    const producer = pdfDoc.getProducer() || undefined;
    const creationDate = pdfDoc.getCreationDate()?.toISOString() || undefined;
    const modificationDate = pdfDoc.getModificationDate()?.toISOString() || undefined;
    
    const pageCount = pdfDoc.getPageCount();
    
    // Extract text content using pdf-parse
    const pdfParse = await import('pdf-parse');
    const result = await (pdfParse.default ?? (pdfParse as any))(Buffer.from(arrayBuffer));
    
    // Split text by pages (pdf-parse gives us all text, we'll split by form feeds)
    const textByPages = result.text ? result.text.split(/\f/g) : [];
    
    const pages: PageData[] = [];
    
    for (let i = 0; i < pageCount; i++) {
      const page = pdfDoc.getPage(i);
      const { width, height } = page.getSize();
      
      // Get text for this page
      const pageText = textByPages[i] || '';
      const lines = pageText.split(/\r?\n/).filter(line => line.trim().length > 0);
      
      // Create text blocks from actual content
      const textBlocks: TextBlock[] = lines.map((line, lineIndex) => ({
        text: line.trim(),
        x: 50,
        y: height - 50 - (lineIndex * 20), // Stack lines vertically
        width: Math.min(line.length * 8, width - 100), // Estimate width
        height: 16,
        fontSize: 12,
        fontFamily: 'Arial',
        fontWeight: 'normal',
        fontStyle: 'normal',
        color: '#000000',
        rotation: 0,
        direction: 'ltr',
        hasEOL: lineIndex < lines.length - 1
      }));
      
      // If no text found, add a placeholder
      if (textBlocks.length === 0) {
        textBlocks.push({
          text: `Page ${i + 1} - No text content detected`,
          x: 50,
          y: height - 50,
          width: 300,
          height: 20,
          fontSize: 12,
          fontFamily: 'Arial',
          fontWeight: 'normal',
          fontStyle: 'normal',
          color: '#666666',
          rotation: 0,
          direction: 'ltr',
          hasEOL: false
        });
      }
      
      // Create placeholder for images
      const images: ImageBlock[] = [
        {
          x: 0,
          y: 0,
          width: width,
          height: height,
          rotation: 0,
          description: `Page ${i + 1} visual content`
        }
      ];
      
      pages.push({
        pageNumber: i + 1,
        width: Math.round(width * 100) / 100,
        height: Math.round(height * 100) / 100,
        textBlocks,
        images
      });
    }
    
    // Create metadata
    const metadata = {
      title: title || fileName.replace('.pdf', ''),
      author: author || 'Unknown',
      subject: subject || 'PDF Document',
      creator: creator || 'PDF Parser',
      producer: producer || 'pdf-lib',
      creationDate: creationDate || new Date().toISOString(),
      modificationDate: modificationDate || new Date().toISOString(),
      numPages: pageCount
    };
    
    const xmlContent = createPdfXml(fileName, metadata, pages);
    
    return new Response(JSON.stringify({
      fileName,
      xmlContent
    }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
    
  } catch (err: any) {
    console.error("PDF parsing error:", err);
    return new Response(JSON.stringify({ error: err?.message || "Failed to parse PDF" }), { status: 500 });
  }
}