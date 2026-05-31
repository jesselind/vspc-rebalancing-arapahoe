import { NextResponse } from "next/server";
import { MAP_PDF_FILENAME, MAP_PDF_SOURCE_URL } from "@/lib/map-pdf-url";
import { clientIp, enforceRateLimit, rateLimitHeaders, rateLimitSettings } from "@/lib/rate-limit";

export async function GET(request: Request) {
  const { limit } = rateLimitSettings("mapPdf");
  const rate = await enforceRateLimit("mapPdf", request);
  if (!rate.allowed) {
    return NextResponse.json(
      { error: "Too many map PDF requests. Please try again later." },
      { status: 429, headers: rateLimitHeaders(rate, limit) },
    );
  }

  const url = new URL(request.url);
  const asAttachment = url.searchParams.get("disposition") === "attachment";

  try {
    const upstream = await fetch(MAP_PDF_SOURCE_URL);
    if (!upstream.ok) {
      return NextResponse.json({ error: "Map PDF unavailable." }, { status: 502 });
    }

    const headers = new Headers(rateLimitHeaders(rate, limit));
    headers.set("Content-Type", "application/pdf");
    headers.set("X-Content-Type-Options", "nosniff");
    headers.set("Cache-Control", "public, max-age=3600");
    if (asAttachment) {
      headers.set("Content-Disposition", `attachment; filename="${MAP_PDF_FILENAME.replace(/"/g, "")}"`);
    } else {
      headers.set("Content-Disposition", "inline");
    }

    const contentLength = upstream.headers.get("content-length");
    if (contentLength) {
      headers.set("Content-Length", contentLength);
    }

    return new NextResponse(upstream.body, { status: 200, headers });
  } catch {
    console.error(`Map PDF proxy failed (${clientIp(request)})`);
    return NextResponse.json({ error: "Map PDF unavailable." }, { status: 502 });
  }
}
