import { NextResponse } from "next/server";
import { csvFileContents } from "@/lib/generated/home-data";
import { ALLOWED_CSV_FILES } from "@/lib/downloads";
import {
  clientIp,
  enforceRateLimit,
  rateLimitHeaders,
  rateLimitSettings,
  STATIC_PUBLIC_CACHE_HEADERS,
} from "@/lib/rate-limit";

export async function GET(request: Request) {
  const { limit } = rateLimitSettings("download");
  const rate = await enforceRateLimit("download", request);
  if (!rate.allowed) {
    return NextResponse.json(
      { error: "Too many download requests. Please try again later." },
      { status: 429, headers: rateLimitHeaders(rate, limit) },
    );
  }

  const url = new URL(request.url);
  const file = url.searchParams.get("file");
  const asAttachment = url.searchParams.get("disposition") === "attachment";

  if (!file || !ALLOWED_CSV_FILES.has(file)) {
    return NextResponse.json({ error: "Missing or disallowed file parameter." }, { status: 400 });
  }

  const raw = csvFileContents[file];
  if (!raw) {
    return NextResponse.json({ error: "File not found." }, { status: 404 });
  }

  try {
    const headers = new Headers(rateLimitHeaders(rate, limit));
    headers.set("Content-Type", "text/csv; charset=utf-8");
    headers.set("X-Content-Type-Options", "nosniff");
    for (const [header, value] of Object.entries(STATIC_PUBLIC_CACHE_HEADERS)) {
      headers.set(header, value);
    }
    if (asAttachment) {
      headers.set("Content-Disposition", `attachment; filename="${file.replace(/"/g, "")}"`);
    } else {
      headers.set("Content-Disposition", "inline");
    }

    return new NextResponse(new TextEncoder().encode(raw), { status: 200, headers });
  } catch {
    console.error(`Download failed for ${file} (${clientIp(request)})`);
    return NextResponse.json({ error: "File not found." }, { status: 404 });
  }
}
