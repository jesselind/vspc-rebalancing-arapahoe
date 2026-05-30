"use client";

import { useState } from "react";
import { MailIcon } from "@/components/icons";
import { Button } from "@/components/ui/button";

type FeedbackPayload = {
  email: string;
  mailto: string;
};

export function FeedbackButton() {
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function openFeedback() {
    setStatus("loading");
    setErrorMessage(null);

    try {
      const response = await fetch("/api/feedback", { method: "GET", cache: "no-store" });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { error?: string } | null;
        throw new Error(body?.error ?? "Unable to open contact email right now.");
      }

      const payload = (await response.json()) as FeedbackPayload;
      window.location.assign(payload.mailto);
      setStatus("idle");
    } catch (error) {
      setStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "Unable to open contact email right now.");
    }
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <Button
        type="button"
        variant="secondary"
        className="!w-auto"
        onClick={() => void openFeedback()}
        disabled={status === "loading"}
        aria-busy={status === "loading"}
      >
        <MailIcon className="size-5" />
        {status === "loading" ? "Opening email..." : "Email support"}
      </Button>
      {errorMessage && (
        <p className="text-sm text-red-700" role="alert">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
