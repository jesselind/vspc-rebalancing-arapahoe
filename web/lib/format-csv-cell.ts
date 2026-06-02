import {
  PRECINCT_MAP_URL_HEADER,
  PROPORTION_PERCENT_HEADERS,
} from "@/lib/csv-reports";

export { PRECINCT_MAP_URL_HEADER } from "@/lib/csv-reports";

export function formatCsvHeader(header: string): string {
  if (header === PRECINCT_MAP_URL_HEADER) {
    return "Precinct Map";
  }
  return header;
}

export function formatCsvCell(header: string, raw: string): string {
  const value = raw ?? "";
  if (!value.trim() || !PROPORTION_PERCENT_HEADERS.has(header)) {
    return value;
  }

  const n = Number(value);
  if (Number.isNaN(n)) {
    return value;
  }

  return `${Math.round(n * 100)}%`;
}
