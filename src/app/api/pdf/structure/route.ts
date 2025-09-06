import { NextRequest } from "next/server";
import type { PdfStructure } from "@/lib/pdf/structure";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get("file");
    if (!file || !(file instanceof Blob)) {
      return new Response(JSON.stringify({ error: "Missing file" }), { status: 400 });
    }
    console.log("file 123", file)

    const arrayBuffer = await file.arrayBuffer();
    console.log("arrayBuffer 123", arrayBuffer)
    const { PDFDocument } = await import("pdf-lib");
    const pdfDoc = await PDFDocument.load(Buffer.from(arrayBuffer));
    console.log("pdfDoc 123", pdfDoc)
    const pageCount = pdfDoc.getPageCount();
    console.log("pageCount 123", pageCount)
    const pages: PdfStructure["pages"] = [];
    for (let i = 0; i < pageCount; i++) {
      const page = pdfDoc.getPage(i);
      console.log(`page ${i} 123`, page)
      const { width, height } = page.getSize();
      pages.push({ pageNumber: i + 1, width, height, textBlocks: [] });
    }

    const structure: PdfStructure = {
      version: 1,
      document: {
        title: null,
        author: null,
        subject: null,
        keywords: null,
        creator: null,
        producer: null,
        creationDate: null,
        modificationDate: null,
        numPages: pages.length,
      },
      pages,
      original: {
        base64: Buffer.from(new Uint8Array(arrayBuffer)).toString("base64"),
        fileName: (file as any).name ?? "document.pdf",
        contentType: file.type || "application/pdf",
        byteLength: (arrayBuffer as ArrayBuffer).byteLength,
      },
    };

    console.log("structure 123", structure)

    return new Response(JSON.stringify(structure), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err?.message || "Failed to parse PDF" }), { status: 500 });
  }
}


