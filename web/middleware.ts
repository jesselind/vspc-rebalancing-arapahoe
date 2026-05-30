import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { isProbePath } from "@/lib/security-paths";

/** Block legacy direct static paths; assets are served only via rate-limited API routes. */
const BLOCKED_PREFIXES = ["/data/", "/maps/"];

const GET_ONLY_API_PATHS = new Set(["/api/download", "/api/feedback"]);

function notFoundResponse() {
  return NextResponse.json({ error: "Not found." }, { status: 404 });
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (isProbePath(pathname)) {
    return notFoundResponse();
  }

  if (BLOCKED_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return notFoundResponse();
  }

  if (GET_ONLY_API_PATHS.has(pathname) && request.method !== "GET") {
    return NextResponse.json(
      { error: "Method not allowed." },
      { status: 405, headers: { Allow: "GET" } },
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
