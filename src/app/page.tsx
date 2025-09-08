"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { RichPasteArea } from "@/components/rich-paste-area";
import type { PdfXmlStructure } from "@/lib/pdf/structure";

export default function Home() {
  const [pastedHtml, setPastedHtml] = useState<string>("");
  const [fileNames, setFileNames] = useState<string[]>([]);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [xmlStructure, setXmlStructure] = useState<PdfXmlStructure | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  return (
    <div className="font-sans min-h-screen p-6 md:p-10">
      <div className="mx-auto w-full max-w-3xl">
        <h1 className="text-2xl font-semibold mb-4">Authless Paste & Upload</h1>
        <p className="text-sm text-muted-foreground mb-6">
          Paste text with formatting preserved or upload PDF files.
        </p>

        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="paste">Paste content (format preserved)</Label>
            <RichPasteArea
              placeholder="Paste here (Ctrl/Cmd + V)"
              onChange={setPastedHtml}
              className="min-h-48"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="files">Upload documents (PDF)</Label>
            <Input
              id="files"
              type="file"
              // single file for now
              accept="application/pdf"
              onChange={(e) => {
                const files = Array.from(e.target.files || []);
                const first = files[0] || null;
                setPdfFile(first);
                setFileNames(first ? [first.name] : []);
              }}
            />
            {fileNames.length > 0 ? (
              <ul className="text-sm text-muted-foreground list-disc pl-5">
                {fileNames.map((n) => (
                  <li key={n}>{n}</li>
                ))}
              </ul>
            ) : null}
          </div>

          <div className="flex items-center gap-3">
            <Button
              disabled={isLoading}
              onClick={async () => {
                if (!pdfFile) {
                  alert("Please select a PDF file first.");
                  return;
                }
                setIsLoading(true);
                try {
                  const form = new FormData();
                  form.append("file", pdfFile, pdfFile.name);
                  const res = await fetch("/api/pdf/structure", { method: "POST", body: form });
                  if (!res.ok) {
                    const data = await res.json().catch(() => ({}));
                    throw new Error(data.error || `Request failed (${res.status})`);
                  }
                  const data = (await res.json()) as PdfXmlStructure;
                  setXmlStructure(data);
                } catch (err: any) {
                  console.error(err);
                  alert(err?.message || "Failed to extract structure");
                } finally {
                  setIsLoading(false);
                }
              }}
            >
              Submit
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setPastedHtml("");
                setFileNames([]);
                setPdfFile(null);
                setXmlStructure(null);
                // Clear visual content by reloading route state
                location.reload();
              }}
            >
              Reset
            </Button>
          </div>

          <div className="space-y-2">
            <Label>Preview (HTML)</Label>
            <div className="rounded-md border border-input p-3 text-sm max-h-60 overflow-auto bg-secondary">
              <pre className="whitespace-pre-wrap break-words">{pastedHtml}</pre>
            </div>
          </div>

          {xmlStructure ? (
            <div className="space-y-2">
              <Label>PDF Structure (XML)</Label>
              <div className="rounded-md border border-input p-3 text-xs max-h-80 overflow-auto bg-secondary">
                <pre className="whitespace-pre-wrap break-words">{xmlStructure.xmlContent}</pre>
              </div>
              <div>
                <Button
                  variant="outline"
                  disabled={isLoading}
                  onClick={async () => {
                    if (!xmlStructure) return;
                    try {
                      const res = await fetch("/api/pdf/generate", {
                        method: "POST",
                        headers: { "content-type": "application/json" },
                        body: JSON.stringify(xmlStructure),
                      });
                      if (!res.ok) {
                        const data = await res.json().catch(() => ({}));
                        throw new Error(data.error || `Request failed (${res.status})`);
                      }
                      const blob = await res.blob();
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = xmlStructure.fileName.replace('.pdf', '.xml');
                      document.body.appendChild(a);
                      a.click();
                      a.remove();
                      URL.revokeObjectURL(url);
                    } catch (err: any) {
                      console.error(err);
                      alert(err?.message || "Failed to download XML");
                    }
                  }}
                >
                  Download XML
                </Button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
