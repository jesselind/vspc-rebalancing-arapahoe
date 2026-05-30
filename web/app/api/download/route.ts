import { readFile } from "node:fs/promises";
import { NextResponse } from "next/server";
import {
  MAP_ASSET_ID,
  MAP_FILE_NAME,
  resolveCsvDownloadPath,
  resolveMapDownloadPath,
} from "@/lib/downloads";
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

  let filePath: string | null = null;
  let fileName: string;

  if (asset === MAP_ASSET_ID) {
    filePath = resolveMapDownloadPath();
    fileName = MAP_FILE_NAME;
  } else if (file) {
    filePath = resolveCsvDownloadPath(file);
    fileName = file;
  } else {
    return NextResponse.json({ error: "Missing file or asset parameter." }, { status: 400 });
  }

  if (!filePath) {
    return NextResponse.json({ error: "File not allowed." }, { status: 400 });
  }

  try {
    const bytes = await readFile(filePath);
    const headers = new Headers(rateLimitHeaders(rate, limit));
    headers.set("Content-Type", mimeFor(fileName));
    headers.set("X-Content-Type-Options", "nosniff");
    headers.set("Cache-Control", "private, no-store");
    if (asAttachment) {
      headers.set("Content-Disposition", `attachment; filename="${fileName.replace(/"/g, "")}"`);
    } else {
      headers.set("Content-Disposition", "inline");
    }

    return new NextResponse(bytes, { status: 200, headers });
  } catch {
    console.error(`Download failed for ${fileName} (${clientIp(request)})`);
    return NextResponse.json({ error: "File not found." }, { status: 404 });
  }
}
