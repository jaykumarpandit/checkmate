import { NextRequest } from "next/server";
import { spawn } from "child_process";
import { join } from "path";

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
    
    console.log(`Processing PDF with Python parser: ${fileName}`);
    
    // Path to Python script
    const pythonScriptPath = join(process.cwd(), "python_pdf_parser", "api_wrapper.py");
    const pythonVenvPath = join(process.cwd(), "python_pdf_parser", "venv", "bin", "python");
    
    // Create promise to handle Python process
    const result = await new Promise<{ success?: boolean; xml_content?: string; metadata?: any; error?: string; extraction_method?: string }>((resolve, reject) => {
      const pythonProcess = spawn(pythonVenvPath, [pythonScriptPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      let stderr = '';
      
      // Send PDF data to Python process
      pythonProcess.stdin.write(Buffer.from(arrayBuffer));
      pythonProcess.stdin.end();
      
      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });
      
      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout);
            resolve(result);
          } catch (parseErr) {
            console.error("Failed to parse Python output:", parseErr);
            resolve({ error: "Failed to parse Python output", extraction_method: "failed" });
          }
        } else {
          console.error("Python process failed:", stderr);
          resolve({ error: `Python process failed with code ${code}: ${stderr}`, extraction_method: "failed" });
        }
      });
      
      pythonProcess.on('error', (err) => {
        console.error("Python process error:", err);
        resolve({ error: `Python process error: ${err.message}`, extraction_method: "failed" });
      });
      
      // Timeout after 30 seconds
      setTimeout(() => {
        pythonProcess.kill();
        resolve({ error: "PDF processing timeout", extraction_method: "timeout" });
      }, 30000);
    });
    
    if (result.error) {
      console.error("Python PDF processing failed:", result.error);
      return new Response(JSON.stringify({
        error: result.error,
        fileName,
        extractionMethod: result.extraction_method
      }), { status: 500 });
    }
    
    console.log("Python PDF processing completed successfully");
    console.log("Metadata:", result.metadata);
    console.log("Extraction method:", result.extraction_method);
    
    return new Response(JSON.stringify({
      fileName,
      xmlContent: result.xml_content,
      metadata: result.metadata,
      extractionMethod: result.extraction_method,
      success: true
    }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
    
  } catch (err: any) {
    console.error("API error:", err);
    return new Response(JSON.stringify({ 
      error: err?.message || "Failed to process PDF",
      extractionMethod: "api-error"
    }), { status: 500 });
  }
}
