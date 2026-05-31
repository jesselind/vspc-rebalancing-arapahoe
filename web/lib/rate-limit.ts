type RateLimitResult = {
  allowed: boolean;
  remaining: number;
  retryAfterSeconds: number;
};

type WindowState = {
  count: number;
  windowStartMs: number;
};

const memoryWindows = new Map<string, WindowState>();

export type RateLimitBucket = "download" | "mapPdf" | "feedback";

function getLimits() {
  const windowSec = Number(process.env.RATE_LIMIT_WINDOW_SECONDS ?? "60");
  const mapPdfWindowSec = Number(process.env.RATE_LIMIT_MAP_PDF_WINDOW_SECONDS ?? "60");
  return {
    windowSec: Number.isFinite(windowSec) && windowSec > 0 ? windowSec : 60,
    downloadMax: Math.max(1, Number(process.env.RATE_LIMIT_DOWNLOAD_MAX ?? "10")),
    mapPdfWindowSec: Number.isFinite(mapPdfWindowSec) && mapPdfWindowSec > 0 ? mapPdfWindowSec : 60,
    mapPdfMax: Math.max(1, Number(process.env.RATE_LIMIT_MAP_PDF_MAX ?? "2")),
    feedbackMax: Math.max(1, Number(process.env.RATE_LIMIT_FEEDBACK_MAX ?? "1")),
  };
}

export function rateLimitSettings(bucket: RateLimitBucket): { limit: number; windowSec: number } {
  const limits = getLimits();
  if (bucket === "mapPdf") {
    return { limit: limits.mapPdfMax, windowSec: limits.mapPdfWindowSec };
  }
  if (bucket === "download") {
    return { limit: limits.downloadMax, windowSec: limits.windowSec };
  }
  return { limit: limits.feedbackMax, windowSec: limits.windowSec };
}

function checkMemoryWindow(key: string, limit: number, windowSec: number): RateLimitResult {
  const now = Date.now();
  const windowMs = windowSec * 1000;
  const existing = memoryWindows.get(key);

  if (!existing || now - existing.windowStartMs >= windowMs) {
    memoryWindows.set(key, { count: 1, windowStartMs: now });
    return { allowed: true, remaining: limit - 1, retryAfterSeconds: windowSec };
  }

  if (existing.count >= limit) {
    const retryAfterSeconds = Math.max(
      1,
      Math.ceil((windowMs - (now - existing.windowStartMs)) / 1000),
    );
    return { allowed: false, remaining: 0, retryAfterSeconds };
  }

  existing.count += 1;
  return {
    allowed: true,
    remaining: limit - existing.count,
    retryAfterSeconds: windowSec,
  };
}

async function checkCacheWindow(
  key: string,
  limit: number,
  windowSec: number,
): Promise<RateLimitResult | null> {
  const cacheStorage = globalThis.caches as (CacheStorage & { default?: Cache }) | undefined;
  const cache = cacheStorage?.default;
  if (!cache) {
    return null;
  }

  const cacheKey = new Request(`https://cei-rate-limit.local/${encodeURIComponent(key)}`);
  const now = Date.now();
  const windowMs = windowSec * 1000;

  const cached = await cache.match(cacheKey);
  let state: WindowState = { count: 0, windowStartMs: now };

  if (cached) {
    try {
      const parsed = (await cached.json()) as WindowState;
      if (now - parsed.windowStartMs < windowMs) {
        state = parsed;
      }
    } catch {
      // Ignore corrupt cache entries and start a new window.
    }
  }

  if (state.count >= limit) {
    const retryAfterSeconds = Math.max(
      1,
      Math.ceil((windowMs - (now - state.windowStartMs)) / 1000),
    );
    return { allowed: false, remaining: 0, retryAfterSeconds };
  }

  state.count += 1;
  await cache.put(
    cacheKey,
    new Response(JSON.stringify(state), {
      headers: {
        "Cache-Control": `max-age=${windowSec}`,
        "Content-Type": "application/json",
      },
    }),
  );

  return {
    allowed: true,
    remaining: limit - state.count,
    retryAfterSeconds: windowSec,
  };
}

export function clientIp(request: Request): string {
  const cfIp = request.headers.get("cf-connecting-ip");
  if (cfIp) {
    return cfIp;
  }

  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) {
    return forwarded.split(",")[0]?.trim() || "unknown";
  }

  return "unknown";
}

export async function enforceRateLimit(
  bucket: RateLimitBucket,
  request: Request,
): Promise<RateLimitResult> {
  const { limit, windowSec } = rateLimitSettings(bucket);
  const key = `${bucket}:${clientIp(request)}`;

  const cacheResult = await checkCacheWindow(key, limit, windowSec);
  if (cacheResult) {
    return cacheResult;
  }

  return checkMemoryWindow(key, limit, windowSec);
}

export function rateLimitHeaders(result: RateLimitResult, limit: number): HeadersInit {
  return {
    "Retry-After": String(result.retryAfterSeconds),
    "X-RateLimit-Limit": String(limit),
    "X-RateLimit-Remaining": String(Math.max(0, result.remaining)),
  };
}
