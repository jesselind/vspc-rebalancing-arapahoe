"use client";

import {
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type CSSProperties,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { InformationCircleIcon } from "@/components/icons";

type Props = {
  label: string;
  children: ReactNode;
};

const VIEWPORT_MARGIN = 12;
const GAP = 8;

function getFocusableElement(container: HTMLElement): HTMLElement | null {
  return container.querySelector<HTMLElement>(
    'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
  );
}

function useCanPortal() {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}

export function InfoPopover({ label, children }: Props) {
  const panelId = useId();
  const [open, setOpen] = useState(false);
  const [coords, setCoords] = useState<{ top: number; left: number } | null>(null);
  const containerRef = useRef<HTMLSpanElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const wasOpenRef = useRef(false);
  const canPortal = useCanPortal();

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

  useLayoutEffect(() => {
    if (!open) {
      return;
    }

    const panel = panelRef.current;
    if (!panel) {
      return;
    }

    const focusTarget = getFocusableElement(panel) ?? panel;
    if (focusTarget === panel) {
      panel.tabIndex = -1;
    }
    focusTarget.focus();
  }, [open, coords]);

  useEffect(() => {
    if (wasOpenRef.current && !open) {
      buttonRef.current?.focus();
    }
    wasOpenRef.current = open;
  }, [open]);

  useEffect(() => {
    if (!open) {
      return;
    }

    function closeOnPointerDown(event: PointerEvent) {
      const target = event.target as Node;
      if (containerRef.current?.contains(target) || panelRef.current?.contains(target)) {
        return;
      }
      setOpen(false);
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        setOpen(false);
      }
    }

    document.addEventListener("pointerdown", closeOnPointerDown);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnPointerDown);
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
        aria-controls={canPortal ? panelId : undefined}
        onClick={() => setOpen((value) => !value)}
      >
        <InformationCircleIcon className="size-5" />
      </button>

      {canPortal &&
        createPortal(
          <div
            ref={panelRef}
            id={panelId}
            role="dialog"
            aria-modal="false"
            aria-label={label}
            aria-hidden={!open}
            inert={!open ? true : undefined}
            style={panelStyle}
            className={`fixed z-50 w-[min(16rem,calc(100vw-2rem))] rounded-lg border border-zinc-200 bg-white p-3 text-sm leading-relaxed text-zinc-700 shadow-lg ${
              open ? "" : "pointer-events-none"
            }`}
          >
            {children}
          </div>,
          document.body,
        )}
    </span>
  );
}
