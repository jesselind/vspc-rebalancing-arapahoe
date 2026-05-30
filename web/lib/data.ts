import { readFile } from "node:fs/promises";
import path from "node:path";
import { parseCsv } from "./csv";
import { contentDataDir } from "./downloads";
import type { CsvDataset, PrecinctAssignment } from "./types";

const DATASETS: Array<{ id: string; label: string; fileName: string }> = [
  { id: "vspc-locations", label: "VSPC Locations", fileName: "VSPC Locations.csv" },
  {
    id: "vspc-precinct-distribution",
    label: "VSPC - Precinct Distribution",
    fileName: "VSPC - Precinct Distribution.csv",
  },
  {
    id: "dc-assignment-verification",
    label: "DC Assignment Verification",
    fileName: "DC Assignment Verification.csv",
  },
  { id: "summary-statistics", label: "Summary Statistics", fileName: "Summary Statistics.csv" },
];

async function readDataset(fileName: string): Promise<string> {
  const fullPath = path.join(contentDataDir(), fileName);
  return readFile(fullPath, "utf8");
}

export async function loadDatasets(): Promise<CsvDataset[]> {
  const entries = await Promise.all(
    DATASETS.map(async ({ id, label, fileName }) => {
      const raw = await readDataset(fileName);
      const rows = parseCsv(raw);
      const [headers, ...body] = rows;
      if (!headers) {
        return null;
      }
      return { id, label, fileName, headers, rows: body } satisfies CsvDataset;
    }),
  );

  return entries.filter((entry): entry is CsvDataset => entry !== null);
}

export async function loadPrecinctAssignments(): Promise<Map<string, PrecinctAssignment>> {
  const raw = await readDataset("VSPC - Precinct Distribution.csv");
  const [headers, ...rows] = parseCsv(raw);
  if (!headers) {
    return new Map();
  }

  const index = Object.fromEntries(headers.map((header, i) => [header.trim(), i]));
  const requiredHeaders = [
    "Precinct",
    "Assigned VSPC",
    "Address",
    "City",
    "State",
    "Zip",
    "Distance to Assigned VSPC (mi.)",
  ];

  for (const header of requiredHeaders) {
    if (typeof index[header] !== "number") {
      return new Map();
    }
  }

  const assignments = new Map<string, PrecinctAssignment>();
  for (const row of rows) {
    const precinct = row[index["Precinct"]]?.trim();
    if (!precinct) {
      continue;
    }
    assignments.set(precinct, {
      precinct,
      assignedVspc: row[index["Assigned VSPC"]] ?? "",
      address: row[index["Address"]] ?? "",
      city: row[index["City"]] ?? "",
      state: row[index["State"]] ?? "",
      zip: row[index["Zip"]] ?? "",
      distanceMiles: row[index["Distance to Assigned VSPC (mi.)"]] ?? "",
    });
  }

  return assignments;
}