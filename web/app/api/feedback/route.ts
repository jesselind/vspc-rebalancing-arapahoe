import { NextResponse } from "next/server";
import { FEEDBACK_EMAIL, FEEDBACK_MAILTO } from "@/lib/feedback";
import { enforceRateLimit, rateLimitHeaders, rateLimitSettings } from "@/lib/rate-limit";

export async function GET(request: Request) {
  const { limit } = rateLimitSettings("feedback");
  const rate = await enforceRateLimit("feedback", request);
  if (!rate.allowed) {
    return NextResponse.json(
      { error: "Too many contact requests. Please try again later." },
      { status: 429, headers: rateLimitHeaders(rate, limit) },
    );
  }

  return NextResponse.json(
    { email: FEEDBACK_EMAIL, mailto: FEEDBACK_MAILTO },
    {
      status: 200,
      headers: {
        ...rateLimitHeaders(rate, limit),
        "Cache-Control": "private, no-store",
      },
    },
  );
}
