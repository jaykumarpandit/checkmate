declare module "pdf-parse" {
  interface PdfParseResult {
    numpages?: number;
    numrender?: number;
    info?: Record<string, unknown>;
    metadata?: unknown;
    text?: string;
    version?: string;
  }

  function pdfParse(data: Buffer | Uint8Array | ArrayBuffer, options?: Record<string, unknown>): Promise<PdfParseResult>;
  export = pdfParse;
}

declare module "pdfjs-dist" {
  export const getDocument: any;
  export const GlobalWorkerOptions: any;
  export const version: string;
}



