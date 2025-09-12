import { NextRequest } from "next/server";
import { spawn } from "child_process";
import { join } from "path";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { xmlContent, fileName } = body;
    
    if (!xmlContent) {
      return new Response(JSON.stringify({ error: "Missing XML content" }), { status: 400 });
    }

    const outputFileName = fileName || "converted.pdf";
    
    console.log(`Converting XML to PDF: ${outputFileName}`);
    
    // Path to Python script
    const pythonScriptPath = join(process.cwd(), "python_pdf_parser", "xml_to_pdf_api.py");
    const pythonVenvPath = join(process.cwd(), "python_pdf_parser", "venv", "bin", "python");
    
    // Create promise to handle Python process
    const result = await new Promise<{ success?: boolean; pdf_data?: string; filename?: string; size?: number; error?: string; conversion_method?: string }>((resolve, reject) => {
      const pythonProcess = spawn(pythonVenvPath, [pythonScriptPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      let stderr = '';
      
      // Send JSON data to Python process
      const inputData = JSON.stringify({
        xmlContent,
        fileName: outputFileName
      });
      
      pythonProcess.stdin.write(inputData);
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
            resolve({ error: "Failed to parse Python output" });
          }
        } else {
          console.error("Python process failed:", stderr);
          resolve({ error: `Python process failed with code ${code}: ${stderr}` });
        }
      });
      
      pythonProcess.on('error', (err) => {
        console.error("Python process error:", err);
        resolve({ error: `Python process error: ${err.message}` });
      });
      
      // Timeout after 30 seconds
      setTimeout(() => {
        pythonProcess.kill();
        resolve({ error: "PDF conversion timeout" });
      }, 30000);
    });
    
    if (result.error) {
      console.error("Python PDF conversion failed:", result.error);
      return new Response(JSON.stringify({
        error: result.error
      }), { status: 500 });
    }
    
    if (!result.pdf_data) {
      console.error("No PDF data returned from Python");
      return new Response(JSON.stringify({
        error: "No PDF data generated"
      }), { status: 500 });
    }
    
    console.log("Python PDF conversion completed successfully");
    console.log(`Generated PDF size: ${result.size} bytes`);
    console.log("Conversion method:", result.conversion_method);
    
    // Convert base64 to buffer
    const pdfBuffer = Buffer.from(result.pdf_data, 'base64');
    
    return new Response(pdfBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${result.filename}"`,
        'Content-Length': pdfBuffer.length.toString(),
      },
    });
    
  } catch (err: any) {
    console.error("API error:", err);
    return new Response(JSON.stringify({ 
      error: err?.message || "Failed to convert XML to PDF"
    }), { status: 500 });
  }
}
