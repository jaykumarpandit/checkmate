import { NextRequest } from "next/server";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  try {
    const { xmlContent } = await req.json();
    
    if (!xmlContent) {
      return new Response(JSON.stringify({ error: "Missing XML content" }), { status: 400 });
    }

    // For now, return the XML content as a downloadable file
    // In the future, this could parse the XML and reconstruct a PDF
    return new Response(xmlContent, {
      status: 200,
      headers: {
        "content-type": "application/xml",
        "content-disposition": "attachment; filename=\"document.xml\"",
      },
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err?.message || "Failed to generate file" }), { status: 500 });
  }
}