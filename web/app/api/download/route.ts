import { NextResponse } from "next/server";
import { csvFileContents } from "@/lib/generated/home-data";
import {
  ALLOWED_CSV_FILES,
  MAP_ASSET_ID,
  MAP_FILE_NAME,
} from "@/lib/downloads";
import { fetchMapPdfFromAssets, loadMapPdfBytes } from "@/lib/map-pdf";
import { clientIp, enforceRateLimit, rateLimitHeaders } from "@/lib/rate-limit";

const MIME_BY_EXT: Record<string, string> = {
  ".csv": "text/csv; charset=utf-8",
  ".pdf": "application/pdf",
};

function mimeFor(fileName: string): string {
  const ext = fileName.slice(fileName.lastIndexOf(".")).toLowerCase();
  return MIME_BY_EXT[ext] ?? "application/octet-stream";
}

export async function GET(request: Request) {
  const limit = Number(process.env.RATE_LIMIT_DOWNLOAD_MAX ?? "30");
  const rate = await enforceRateLimit("download", request);
  if (!rate.allowed) {
    return NextResponse.json(
      { error: "Too many download requests. Please try again later." },
      { status: 429, headers: rateLimitHeaders(rate, limit) },
    );
  }

  const url = new URL(request.url);
  const asset = url.searchParams.get("asset");
  const file = url.searchParams.get("file");
  const asAttachment = url.searchParams.get("disposition") === "attachment";

  const fileName = asset === MAP_ASSET_ID ? MAP_FILE_NAME : (file ?? "download");

  const headers = new Headers(rateLimitHeaders(rate, limit));
  headers.set("Content-Type", mimeFor(fileName));
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("Cache-Control", "private, no-store");
  if (asAttachment) {
    headers.set("Content-Disposition", `attachment; filename="${fileName.replace(/"/g, "")}"`);
  } else {
    headers.set("Content-Disposition", "inline");
  }

  try {
    if (asset === MAP_ASSET_ID) {
      const assetResponse = await fetchMapPdfFromAssets();
      if (assetResponse?.body) {
        const contentLength = assetResponse.headers.get("content-length");
        if (contentLength) {
          headers.set("Content-Length", contentLength);
        }
        return new NextResponse(assetResponse.body, { status: 200, headers });
      }

      const bytes = await loadMapPdfBytes();
      return new NextResponse(Buffer.from(bytes), { status: 200, headers });
    }

    if (file && ALLOWED_CSV_FILES.has(file)) {
      const raw = csvFileContents[file];
      if (!raw) {
        return NextResponse.json({ error: "File not found." }, { status: 404 });
      }
      return new NextResponse(new TextEncoder().encode(raw), { status: 200, headers });
    }

    return NextResponse.json({ error: "Missing file or asset parameter." }, { status: 400 });
  } catch {
    console.error(`Download failed for ${fileName} (${clientIp(request)})`);
    return NextResponse.json({ error: "File not found." }, { status: 404 });
  }
}
