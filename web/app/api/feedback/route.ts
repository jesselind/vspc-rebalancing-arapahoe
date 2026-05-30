import { NextResponse } from "next/server";
import { FEEDBACK_EMAIL, FEEDBACK_MAILTO } from "@/lib/feedback";
import { enforceRateLimit, rateLimitHeaders } from "@/lib/rate-limit";

export async function GET(request: Request) {
  const limit = Number(process.env.RATE_LIMIT_FEEDBACK_MAX ?? "8");
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
