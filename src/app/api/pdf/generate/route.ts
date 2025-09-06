import { NextRequest } from "next/server";
import type { PdfStructure } from "@/lib/pdf/structure";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  try {
    const structure = (await req.json()) as PdfStructure;
    if (!structure?.original?.base64) {
      return new Response(JSON.stringify({ error: "Missing original base64" }), { status: 400 });
    }

    const buffer = Buffer.from(structure.original.base64, "base64");
    return new Response(buffer, {
      status: 200,
      headers: {
        "content-type": structure.original.contentType || "application/pdf",
        "content-disposition": `attachment; filename="${structure.original.fileName || "document.pdf"}"`,
      },
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err?.message || "Failed to generate PDF" }), { status: 500 });
  }
}



