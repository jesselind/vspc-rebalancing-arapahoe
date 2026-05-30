"use client";

import { useMemo, useState } from "react";
import { InfoPopover } from "@/components/info-popover";
import { MagnifyingGlassIcon, MapPinIcon, XMarkIcon } from "@/components/icons";
import { Button, PageSection } from "@/components/ui/button";
import { ARAPAHOE_VOTER_LOOKUP_URL, ARAPAHOE_VSPC_URL } from "@/lib/county-links";
import { formatFullAddress, googleMapsSearchUrl } from "@/lib/maps";
import type { PrecinctAssignment } from "@/lib/types";

const countyLinkClass =
  "font-medium text-blue-700 underline decoration-blue-400 underline-offset-2 hover:text-blue-900";

type Props = {
  assignments: PrecinctAssignment[];
};

export function PrecinctLookup({ assignments }: Props) {
  const [inputValue, setInputValue] = useState("");
  const [query, setQuery] = useState("");
  const assignmentMap = useMemo(
    () => new Map(assignments.map((assignment) => [assignment.precinct, assignment])),
    [assignments],
  );

  const normalized = query.trim();
  const match = normalized ? assignmentMap.get(normalized) : null;
  const hasSubmitted = normalized.length > 0;
  const canClear = inputValue.length > 0 || hasSubmitted;

  function startOver() {
    setInputValue("");
    setQuery("");
  }

  return (
    <PageSection
      title="Find your assigned voting location"
      titleAccessory={
        <InfoPopover label="Official county VSPC locations and hours">
          <p>
            For official county VSPC locations, hours, and services, see{" "}
            <a
              href={ARAPAHOE_VSPC_URL}
              target="_blank"
              rel="noopener noreferrer"
              className={countyLinkClass}
            >
              VSPC locations and hours
              <span className="sr-only"> on the Arapahoe County website (opens in a new tab)</span>
            </a>
            .
          </p>
        </InfoPopover>
      }
      icon={<MagnifyingGlassIcon className="size-6 text-blue-700" />}
    >
      <form
        className="flex flex-row items-end gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          setQuery(inputValue);
        }}
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <label className="text-sm font-medium text-zinc-800" htmlFor="precinct-number">
              Precinct number
            </label>
            <InfoPopover label="Help finding your precinct">
              <p>
                Don&apos;t know your precinct number?{" "}
                <a
                  href={ARAPAHOE_VOTER_LOOKUP_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={countyLinkClass}
                >
                  Look it up with the county registered voter search
                  <span className="sr-only"> (opens in a new tab)</span>
                </a>
                .
              </p>
            </InfoPopover>
          </div>
          <input
            id="precinct-number"
            inputMode="numeric"
            autoComplete="off"
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            placeholder="Example: 101"
            className="mt-2 h-11 w-full rounded-lg border border-zinc-300 bg-white px-3 text-base text-zinc-900 shadow-sm outline-none transition-colors placeholder:text-zinc-400 focus:border-blue-600 focus:ring-2 focus:ring-blue-200"
          />
        </div>
        {canClear && (
          <Button
            type="button"
            variant="secondary"
            className="!w-11 h-11 shrink-0 self-end !px-0"
            aria-label="Clear precinct and start over"
            onClick={startOver}
          >
            <XMarkIcon className="size-5" />
          </Button>
        )}
        <Button type="submit" variant="primary" className="!w-auto h-11 shrink-0 self-end">
          <MagnifyingGlassIcon className="size-4" />
          Find VSPC
        </Button>
      </form>

      {hasSubmitted && !match && (
        <p
          role="alert"
          className="mt-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900"
        >
          No assignment found for precinct &ldquo;{normalized}&rdquo;.
        </p>
      )}

      {match && (
        <div role="status">
          <AssignmentResult assignment={match} />
        </div>
      )}
    </PageSection>
  );
}

function AssignmentResult({ assignment }: { assignment: PrecinctAssignment }) {
  const fullAddress = formatFullAddress(assignment);
  const mapsUrl = fullAddress ? googleMapsSearchUrl(fullAddress) : null;

  return (
    <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4 shadow-sm">
      <p className="text-lg font-semibold text-blue-950">{assignment.assignedVspc}</p>
      {fullAddress && mapsUrl ? (
        <a
          href={mapsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className={`mt-2 inline-flex items-start gap-1.5 ${countyLinkClass}`}
        >
          <MapPinIcon className="mt-0.5 size-4 shrink-0" />
          <span>
            {fullAddress}
            <span className="sr-only"> (opens in Google Maps)</span>
          </span>
        </a>
      ) : (
        <p className="mt-1 text-sm text-blue-900">Address not available.</p>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-1.5 text-sm text-blue-800">
        <span>
          Distance to assigned VSPC: {assignment.distanceMiles || "N/A"} miles
        </span>
        <InfoPopover label="What does distance to assigned VSPC mean?">
          The distance from the geographic center of your precinct to the VSPC location.
        </InfoPopover>
      </div>
    </div>
  );
}
