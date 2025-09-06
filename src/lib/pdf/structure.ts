export type PdfStructure = {
  version: 1;
  document: {
    title?: string | null;
    author?: string | null;
    subject?: string | null;
    keywords?: string[] | null;
    creator?: string | null;
    producer?: string | null;
    creationDate?: string | null;
    modificationDate?: string | null;
    numPages: number;
  };
  pages: Array<{
    pageNumber: number;
    width?: number;
    height?: number;
    textBlocks: Array<{
      str: string;
      x?: number;
      y?: number;
      fontName?: string;
      fontSize?: number;
      dir?: "ltr" | "rtl" | "ttb" | "btt" | string;
    }>;
  }>;
  original?: {
    base64?: string; // Original file for exact reconstruction
    fileName?: string;
    contentType?: string;
    byteLength?: number;
  };
};

export function stringifyPdfStructure(structure: PdfStructure): string {
  return JSON.stringify(structure, null, 2);
}


