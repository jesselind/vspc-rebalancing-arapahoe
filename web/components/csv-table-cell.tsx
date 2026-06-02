import { MapIcon } from "@/components/icons";
import {
  ADDRESS_HEADER,
  ASSIGNED_VSPC_HEADER,
  PRECINCT_DISTRIBUTION_DATASET_ID,
  PRECINCT_MAP_URL_HEADER,
  VSPC_LOCATIONS_DATASET_ID,
  VSPC_MAP_LINK_HEADERS,
} from "@/lib/csv-reports";
import { formatCsvCell } from "@/lib/format-csv-cell";
import {
  googleMapsLinkClass,
  type VspcMapsLookup,
  vspcLocationMapsUrlFromRow,
  vspcNameMapsUrl,
} from "@/lib/maps";

const mapLinkClass =
  "inline-flex size-8 shrink-0 items-center justify-center rounded-md border border-zinc-300 bg-white text-blue-700 shadow-sm transition-colors hover:bg-zinc-50 hover:text-blue-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-500";

function isHttpUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

type Props = {
  header: string;
  value: string;
  precinct?: string;
  datasetId?: string;
  row?: string[];
  headers?: string[];
  vspcMapsByName?: VspcMapsLookup;
};

function GoogleMapsTextLink({
  href,
  children,
  label,
}: {
  href: string;
  children: string;
  label: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={googleMapsLinkClass}
      aria-label={`${label} (opens in a new tab)`}
    >
      {children}
    </a>
  );
}

export function CsvTableCell({
  header,
  value,
  precinct,
  datasetId,
  row,
  headers,
  vspcMapsByName,
}: Props) {
  const trimmed = value.trim();

  if (
    datasetId === PRECINCT_DISTRIBUTION_DATASET_ID &&
    VSPC_MAP_LINK_HEADERS.has(header) &&
    trimmed
  ) {
    const mapsUrl = vspcNameMapsUrl(trimmed, vspcMapsByName);
    if (mapsUrl) {
      return (
        <GoogleMapsTextLink href={mapsUrl} label={`Open ${trimmed} in Google Maps`}>
          {trimmed}
        </GoogleMapsTextLink>
      );
    }
  }

  if (
    datasetId === VSPC_LOCATIONS_DATASET_ID &&
    headers &&
    row &&
    (header === ASSIGNED_VSPC_HEADER || header === ADDRESS_HEADER) &&
    trimmed
  ) {
    const mapsUrl = vspcLocationMapsUrlFromRow(headers, row);
    if (mapsUrl) {
      const label =
        header === ASSIGNED_VSPC_HEADER
          ? `Open ${trimmed} in Google Maps`
          : `Open ${trimmed} address in Google Maps`;

      return <GoogleMapsTextLink href={mapsUrl} label={label}>{trimmed}</GoogleMapsTextLink>;
    }
  }

  if (header === PRECINCT_MAP_URL_HEADER && trimmed && isHttpUrl(trimmed)) {
    const label = precinct
      ? `Open precinct ${precinct} map (PDF)`
      : "Open precinct map (PDF)";

    return (
      <a
        href={trimmed}
        target="_blank"
        rel="noopener noreferrer"
        className={mapLinkClass}
        aria-label={`${label} (opens in a new tab)`}
        title={precinct ? `Precinct ${precinct} map` : "Precinct map"}
      >
        <MapIcon className="size-4" />
      </a>
    );
  }

  return formatCsvCell(header, value);
}
