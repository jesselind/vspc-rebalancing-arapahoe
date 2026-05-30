"use client";

import { useEffect, useState } from "react";
import { ArrowDownTrayIcon, ArrowTopRightOnSquareIcon, MapIcon } from "@/components/icons";
import { ButtonLink, PageSection } from "@/components/ui/button";

const MAP_PDF_API = "/api/download?asset=map";
const MAP_PDF_DOWNLOAD = "/api/download?asset=map&disposition=attachment";

type LoadState = "idle" | "loading" | "loaded" | "error";

export function PdfViewer() {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [progress, setProgress] = useState<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadPdf() {
      try {
        const response = await fetch(MAP_PDF_API, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`Failed to load PDF: ${response.status}`);
        }

        const total = Number(response.headers.get("content-length")) || 0;
        if (!response.body) {
          const fullBlob = await response.blob();
          const fallbackUrl = URL.createObjectURL(fullBlob);
          setBlobUrl((prev) => {
            if (prev) {
              URL.revokeObjectURL(prev);
            }
            return fallbackUrl;
          });
          setLoadState("loaded");
          return;
        }

        const reader = response.body.getReader();
        const chunks: Uint8Array[] = [];
        let loaded = 0;
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            break;
          }
          if (value) {
            chunks.push(value);
            loaded += value.length;
            if (total > 0) {
              setProgress(Math.round((loaded / total) * 100));
            }
          }
        }

        const blob = new Blob(chunks as BlobPart[], { type: "application/pdf" });
        const objectUrl = URL.createObjectURL(blob);
        setBlobUrl((prev) => {
          if (prev) {
            URL.revokeObjectURL(prev);
          }
          return objectUrl;
        });
        setLoadState("loaded");
      } catch {
        if (!controller.signal.aborted) {
          setLoadState("error");
        }
      }
    }

    void loadPdf();

    return () => {
      controller.abort();
    };
  }, []);

  useEffect(() => {
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [blobUrl]);

  return (
    <PageSection title="County map (PDF)" icon={<MapIcon className="size-6 text-blue-700" />}>
      {loadState === "loading" && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <p className="text-sm font-medium text-blue-900">Loading map PDF...</p>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-blue-100">
            <div
              className="h-full rounded-full bg-blue-700 transition-all"
              style={{ width: progress !== null ? `${progress}%` : "35%" }}
            />
          </div>
          <p className="mt-2 text-xs text-blue-800">
            {progress !== null ? `${progress}% loaded` : "Progress not available for this file."}
          </p>
        </div>
      )}

      {loadState === "error" && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">
          Unable to load PDF in this view. Try opening in a new tab or downloading the file.
        </p>
      )}

      {blobUrl && loadState === "loaded" && (
        <iframe
          src={blobUrl}
          title="Full county map PDF"
          className="h-[640px] w-full rounded-lg border border-zinc-200 shadow-inner"
        />
      )}

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        <ButtonLink href={MAP_PDF_API} target="_blank" rel="noopener noreferrer" variant="secondary">
          <ArrowTopRightOnSquareIcon className="size-4" />
          Open in new tab
        </ButtonLink>
        <ButtonLink href={MAP_PDF_DOWNLOAD} variant="secondary">
          <ArrowDownTrayIcon className="size-4" />
          Download PDF
        </ButtonLink>
      </div>
    </PageSection>
  );
}
