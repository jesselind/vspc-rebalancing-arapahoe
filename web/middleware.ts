import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/** Block legacy direct static paths; assets are served only via rate-limited API routes. */
const BLOCKED_PREFIXES = ["/data/", "/maps/", "/cei-map.pdf"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (BLOCKED_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return NextResponse.json({ error: "Not found." }, { status: 404 });
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/data/:path*", "/maps/:path*", "/cei-map.pdf"],
};
