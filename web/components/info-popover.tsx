"use client";

import {
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { InformationCircleIcon } from "@/components/icons";

type Props = {
  label: string;
  children: ReactNode;
};

const VIEWPORT_MARGIN = 12;
const GAP = 8;

export function InfoPopover({ label, children }: Props) {
  const panelId = useId();
  const [open, setOpen] = useState(false);
  const [coords, setCoords] = useState<{ top: number; left: number } | null>(null);
  const containerRef = useRef<HTMLSpanElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!open) {
      return;
    }

    function placePanel() {
      const button = buttonRef.current;
      const panel = panelRef.current;
      if (!button || !panel) {
        return;
      }

      const btnRect = button.getBoundingClientRect();
      const panelWidth = panel.offsetWidth;
      const panelHeight = panel.offsetHeight;

      let left = btnRect.left + btnRect.width / 2 - panelWidth / 2;
      left = Math.max(
        VIEWPORT_MARGIN,
        Math.min(left, window.innerWidth - panelWidth - VIEWPORT_MARGIN),
      );

      let top = btnRect.bottom + GAP;
      if (top + panelHeight > window.innerHeight - VIEWPORT_MARGIN) {
        top = btnRect.top - panelHeight - GAP;
      }
      top = Math.max(VIEWPORT_MARGIN, top);

      setCoords({ top, left });
    }

    placePanel();
    window.addEventListener("resize", placePanel);
    window.addEventListener("scroll", placePanel, true);
    return () => {
      window.removeEventListener("resize", placePanel);
      window.removeEventListener("scroll", placePanel, true);
    };
  }, [open, children]);

  useEffect(() => {
    if (!open) {
      return;
    }

    function closeOnPointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", closeOnPointerDown);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnPointerDown);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  const panelStyle: CSSProperties =
    open && coords
      ? { top: coords.top, left: coords.left }
      : { top: 0, left: 0, visibility: "hidden" };

  return (
    <span ref={containerRef} className="inline-flex">
      <button
        ref={buttonRef}
        type="button"
        className="inline-flex shrink-0 rounded-full text-blue-700 hover:text-blue-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
        aria-label={label}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
      >
        <InformationCircleIcon className="size-5" />
      </button>

      {open && (
        <div
          ref={panelRef}
          id={panelId}
          role="tooltip"
          style={panelStyle}
          className="fixed z-50 w-[min(16rem,calc(100vw-2rem))] rounded-lg border border-zinc-200 bg-white p-3 text-sm leading-relaxed text-zinc-700 shadow-lg"
        >
          {children}
        </div>
      )}
    </span>
  );
}
