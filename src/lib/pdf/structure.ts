export type PdfXmlStructure = {
  fileName: string;
  xmlContent: string;
};

export type TextBlock = {
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
  fontSize: number;
  fontFamily: string;
  fontWeight: string;
  fontStyle: string;
  color: string;
  rotation: number;
  direction: string;
  hasEOL: boolean;
};

export type ImageBlock = {
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  dataUrl?: string;
  description?: string;
};

export type PageData = {
  pageNumber: number;
  width: number;
  height: number;
  textBlocks: TextBlock[];
  images: ImageBlock[];
  background?: string;
};

export function createPdfXml(
  fileName: string,
  metadata: {
    title?: string;
    author?: string;
    subject?: string;
    creator?: string;
    producer?: string;
    creationDate?: string;
    modificationDate?: string;
    numPages: number;
  },
  pages: PageData[]
): string {
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<pdf-document>
  <metadata>
    <title>${escapeXml(metadata.title || '')}</title>
    <author>${escapeXml(metadata.author || '')}</author>
    <subject>${escapeXml(metadata.subject || '')}</subject>
    <creator>${escapeXml(metadata.creator || '')}</creator>
    <producer>${escapeXml(metadata.producer || '')}</producer>
    <creation-date>${escapeXml(metadata.creationDate || '')}</creation-date>
    <modification-date>${escapeXml(metadata.modificationDate || '')}</modification-date>
    <page-count>${metadata.numPages}</page-count>
  </metadata>
  <pages>
    ${pages.map(page => `
    <page number="${page.pageNumber}" width="${page.width}" height="${page.height}">
      <text-blocks>
        ${page.textBlocks.map(block => `
        <text-block 
          x="${block.x}" 
          y="${block.y}" 
          width="${block.width}" 
          height="${block.height}"
          font-size="${block.fontSize}"
          font-family="${escapeXml(block.fontFamily)}"
          font-weight="${block.fontWeight}"
          font-style="${block.fontStyle}"
          color="${escapeXml(block.color)}"
          rotation="${block.rotation}"
          direction="${escapeXml(block.direction)}"
          has-eol="${block.hasEOL}">
          ${escapeXml(block.text)}
        </text-block>`).join('')}
      </text-blocks>
      ${page.images && page.images.length > 0 ? `
      <images>
        ${page.images.map(img => `
        <image 
          x="${img.x}" 
          y="${img.y}" 
          width="${img.width}" 
          height="${img.height}"
          rotation="${img.rotation}"
          ${img.dataUrl ? `data-url="${escapeXml(img.dataUrl)}"` : ''}
          ${img.description ? `description="${escapeXml(img.description)}"` : ''} />`).join('')}
      </images>` : ''}
      ${page.background ? `<background>${escapeXml(page.background)}</background>` : ''}
    </page>`).join('')}
  </pages>
</pdf-document>`;

  return xml;
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}