"use client";

import { useMemo, useRef, useState, type KeyboardEvent } from "react";
import { ArrowDownTrayIcon, DocumentIcon } from "@/components/icons";
import { Button, ButtonLink, PageSection } from "@/components/ui/button";
import { CsvTableCell } from "@/components/csv-table-cell";
import {
  PRECINCT_MAP_URL_HEADER,
  REPORT_DESCRIPTIONS,
  VSPC_LOCATIONS_DATASET_ID,
} from "@/lib/csv-reports";
import { formatCsvHeader } from "@/lib/format-csv-cell";
import { buildVspcMapsLookup } from "@/lib/maps";
import type { CsvDataset } from "@/lib/types";

type Props = {
  datasets: CsvDataset[];
};

function tabId(datasetId: string) {
  return `report-tab-${datasetId}`;
}

function panelId(datasetId: string) {
  return `report-panel-${datasetId}`;
}

export function CsvSection({ datasets }: Props) {
  const [activeId, setActiveId] = useState(datasets[0]?.id ?? "");
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const activeDataset = useMemo(
    () => datasets.find((dataset) => dataset.id === activeId) ?? datasets[0],
    [activeId, datasets],
  );

  const precinctColIndex = useMemo(() => {
    if (!activeDataset) {
      return -1;
    }
    return activeDataset.headers.indexOf("Precinct");
  }, [activeDataset]);

  const vspcMapsByName = useMemo(() => {
    const locations = datasets.find((dataset) => dataset.id === VSPC_LOCATIONS_DATASET_ID);
    if (!locations) {
      return undefined;
    }
    return buildVspcMapsLookup(locations.headers, locations.rows);
  }, [datasets]);

  if (!activeDataset) {
    return null;
  }

  const activeDescription = REPORT_DESCRIPTIONS[activeDataset.id];
  const activeDescriptionId = `${panelId(activeDataset.id)}-description`;

  function focusTab(index: number) {
    tabRefs.current[index]?.focus();
  }

  function selectTab(index: number) {
    const dataset = datasets[index];
    if (!dataset) {
      return;
    }
    setActiveId(dataset.id);
    focusTab(index);
  }

  function onTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    let nextIndex: number | null = null;

    switch (event.key) {
      case "ArrowRight":
        nextIndex = (index + 1) % datasets.length;
        break;
      case "ArrowLeft":
        nextIndex = (index - 1 + datasets.length) % datasets.length;
        break;
      case "Home":
        nextIndex = 0;
        break;
      case "End":
        nextIndex = datasets.length - 1;
        break;
      default:
        return;
    }

    event.preventDefault();
    selectTab(nextIndex);
  }

  return (
    <PageSection title="Reports" icon={<DocumentIcon className="size-6 text-blue-700" />} showDivider={false}>
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap" role="tablist" aria-label="Report datasets">
        {datasets.map((dataset, index) => (
          <Button
            key={dataset.id}
            ref={(element) => {
              tabRefs.current[index] = element;
            }}
            id={tabId(dataset.id)}
            type="button"
            variant={dataset.id === activeDataset.id ? "tabActive" : "tab"}
            onClick={() => setActiveId(dataset.id)}
            role="tab"
            aria-selected={dataset.id === activeDataset.id}
            aria-controls={panelId(dataset.id)}
            tabIndex={dataset.id === activeDataset.id ? 0 : -1}
            onKeyDown={(event) => onTabKeyDown(event, index)}
          >
            {dataset.label}
          </Button>
        ))}
      </div>

      {activeDescription ? (
        <p id={activeDescriptionId} className="mt-4 text-sm text-zinc-600">
          {activeDescription}
        </p>
      ) : null}

      <div
        role="tabpanel"
        id={panelId(activeDataset.id)}
        aria-labelledby={tabId(activeDataset.id)}
        aria-describedby={activeDescription ? activeDescriptionId : undefined}
        tabIndex={0}
        className="mt-3 max-h-[32rem] overflow-auto overscroll-contain rounded-lg border border-zinc-200 bg-zinc-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-500"
      >
        <table className="min-w-full border-separate border-spacing-0">
          <thead>
            <tr>
              {activeDataset.headers.map((header, colIndex) => (
                <th
                  key={header}
                  scope="col"
                  className={`sticky top-0 border-b border-zinc-200 bg-zinc-100 px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-zinc-700 ${
                    colIndex === 0
                      ? "left-0 z-40 min-w-[5.5rem] shadow-[4px_0_6px_-4px_rgba(0,0,0,0.12)]"
                      : header === PRECINCT_MAP_URL_HEADER
                        ? "z-20 w-16 text-center"
                        : "z-20"
                  }`}
                >
                  {formatCsvHeader(header)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {activeDataset.rows.map((row, rowIndex) => (
              <tr key={`${activeDataset.id}-${rowIndex}`} className="odd:bg-white even:bg-zinc-50">
                {activeDataset.headers.map((header, colIndex) => (
                  <td
                    key={`${activeDataset.id}-${rowIndex}-${colIndex}`}
                    className={`border-b border-zinc-100 px-3 py-2 text-sm text-zinc-800 ${
                      colIndex === 0
                        ? `sticky left-0 z-10 min-w-[5.5rem] shadow-[4px_0_6px_-4px_rgba(0,0,0,0.08)] ${
                            rowIndex % 2 === 0 ? "bg-white" : "bg-zinc-50"
                          }`
                        : header === PRECINCT_MAP_URL_HEADER
                          ? "text-center"
                          : ""
                    }`}
                  >
                    <CsvTableCell
                      header={header}
                      value={row[colIndex] ?? ""}
                      precinct={precinctColIndex >= 0 ? row[precinctColIndex] : undefined}
                      datasetId={activeDataset.id}
                      headers={activeDataset.headers}
                      row={row}
                      vspcMapsByName={vspcMapsByName}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4">
        <ButtonLink
          href={`/api/download?file=${encodeURIComponent(activeDataset.fileName)}&disposition=attachment`}
          variant="secondary"
          className="!w-auto"
        >
          <ArrowDownTrayIcon className="size-4" />
          Download {activeDataset.fileName}
        </ButtonLink>
      </div>
    </PageSection>
  );
}
