import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          // CSP omitted in app headers: strict script-src breaks Next.js client hydration in dev.
          // Configure CSP at Cloudflare when deploying if needed.
        ],
      },
    ];
  },
};

export default nextConfig;
