import { NextResponse } from "next/server";
import { MAP_PDF_FILENAME, MAP_PDF_SOURCE_URL } from "@/lib/map-pdf-url";
import {
  clientIp,
  enforceRateLimit,
  getWorkersDefaultCache,
  rateLimitHeaders,
  rateLimitSettings,
  STATIC_PUBLIC_CACHE_HEADERS,
  STATIC_PUBLIC_CACHE_MAX_AGE_SECONDS,
} from "@/lib/rate-limit";

const PDF_BYTES_CACHE_KEY = new Request("https://cei-asset-cache.local/map-pdf");

async function loadPdfBytes(): Promise<ArrayBuffer | null> {
  const cache = getWorkersDefaultCache();
  const cached = cache ? await cache.match(PDF_BYTES_CACHE_KEY) : null;
  if (cached) {
    return cached.arrayBuffer();
  }

  const upstream = await fetch(MAP_PDF_SOURCE_URL);
  if (!upstream.ok) {
    return null;
  }

  const bytes = await upstream.arrayBuffer();
  if (cache) {
    try {
      await cache.put(
        PDF_BYTES_CACHE_KEY,
        new Response(bytes, {
          headers: {
            "Cache-Control": `max-age=${STATIC_PUBLIC_CACHE_MAX_AGE_SECONDS}`,
            "Content-Type": "application/pdf",
          },
        }),
      );
    } catch (error) {
      console.warn("Map PDF cache.put failed:", error);
    }
  }
  return bytes;
}

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
    const bytes = await loadPdfBytes();
    if (!bytes) {
      return NextResponse.json({ error: "Map PDF unavailable." }, { status: 502 });
    }

    const headers = new Headers(rateLimitHeaders(rate, limit));
    headers.set("Content-Type", "application/pdf");
    headers.set("X-Content-Type-Options", "nosniff");
    for (const [header, value] of Object.entries(STATIC_PUBLIC_CACHE_HEADERS)) {
      headers.set(header, value);
    }
    if (asAttachment) {
      headers.set("Content-Disposition", `attachment; filename="${MAP_PDF_FILENAME.replace(/"/g, "")}"`);
    } else {
      headers.set("Content-Disposition", "inline");
    }
    headers.set("Content-Length", String(bytes.byteLength));

    return new NextResponse(bytes, { status: 200, headers });
  } catch {
    console.error(`Map PDF proxy failed (${clientIp(request)})`);
    return NextResponse.json({ error: "Map PDF unavailable." }, { status: 502 });
  }
}
