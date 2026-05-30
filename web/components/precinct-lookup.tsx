"use client";

import { useMemo, useState } from "react";
import { InfoPopover } from "@/components/info-popover";
import { MagnifyingGlassIcon, MapPinIcon } from "@/components/icons";
import { Button, PageSection } from "@/components/ui/button";
import { formatFullAddress, googleMapsSearchUrl } from "@/lib/maps";
import type { PrecinctAssignment } from "@/lib/types";

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

  return (
    <PageSection
      title="Find your assigned VSPC"
      icon={<MagnifyingGlassIcon className="size-6 text-blue-700" />}
    >
      <p className="text-sm text-zinc-600">
        Enter a precinct number to view the assigned VSPC and location details.
      </p>

      <form
        className="mt-4 flex flex-row items-end gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          setQuery(inputValue);
        }}
      >
        <div className="min-w-0 flex-1">
          <label className="block text-sm font-medium text-zinc-800" htmlFor="precinct-number">
            Precinct number
          </label>
          <input
            id="precinct-number"
            inputMode="numeric"
            autoComplete="off"
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            placeholder="Example: 101"
            className="mt-2 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-zinc-900 shadow-sm outline-none transition-colors placeholder:text-zinc-400 focus:border-blue-600 focus:ring-2 focus:ring-blue-200"
          />
        </div>
        <Button type="submit" variant="primary" className="!w-auto shrink-0">
          <MagnifyingGlassIcon className="size-4" />
          Find VSPC
        </Button>
      </form>

      {hasSubmitted && !match && (
        <p className="mt-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          No assignment found for precinct &ldquo;{normalized}&rdquo;.
        </p>
      )}

      {match && <AssignmentResult assignment={match} />}
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
          className="mt-2 inline-flex items-start gap-1.5 text-sm font-medium text-blue-800 underline decoration-blue-400 underline-offset-2 hover:text-blue-950"
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
      <p className="mt-2 flex flex-wrap items-center gap-1.5 text-sm text-blue-800">
        <span>
          Distance to assigned VSPC: {assignment.distanceMiles || "N/A"} miles
        </span>
        <InfoPopover label="What does distance to assigned VSPC mean?">
          The distance from the geographic center of your precinct to the VSPC location.
        </InfoPopover>
      </p>
    </div>
  );
}
