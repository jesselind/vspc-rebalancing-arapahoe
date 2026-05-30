import { existsSync } from "node:fs";
import path from "node:path";

export const MAP_ASSET_ID = "map";

const CONTENT_MARKER = path.join("data", "VSPC Locations.csv");

let cachedContentRoot: string | null = null;

/** Resolve after OpenNext chdirs to server-functions/default (not at module load). */
function contentRoot(): string {
  if (cachedContentRoot) {
    return cachedContentRoot;
  }

  const candidates = [
    path.join(/* turbopackIgnore: true */ process.cwd(), "content"),
    "/bundle/content",
  ];
  for (const root of candidates) {
    if (existsSync(path.join(root, CONTENT_MARKER))) {
      cachedContentRoot = root;
      return root;
    }
  }

  cachedContentRoot = candidates[0];
  return cachedContentRoot;
}

function dataDir(): string {
  return path.join(contentRoot(), "data");
}

function mapsDir(): string {
  return path.join(contentRoot(), "maps");
}

export const ALLOWED_CSV_FILES = new Set([
  "VSPC Locations.csv",
  "VSPC - Precinct Distribution.csv",
  "DC Assignment Verification.csv",
  "Summary Statistics.csv",
]);

export const MAP_FILE_NAME = "full-county-1_50000.pdf";

export function resolveCsvDownloadPath(fileName: string): string | null {
  if (!ALLOWED_CSV_FILES.has(fileName)) {
    return null;
  }
  return path.join(dataDir(), fileName);
}

export function resolveMapDownloadPath(): string {
  return path.join(mapsDir(), MAP_FILE_NAME);
}

export function contentDataDir(): string {
  return dataDir();
}
