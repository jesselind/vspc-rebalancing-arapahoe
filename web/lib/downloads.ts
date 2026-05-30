import path from "node:path";

export const MAP_ASSET_ID = "map";

const DATA_DIR = path.join(/* turbopackIgnore: true */ process.cwd(), "content", "data");
const MAPS_DIR = path.join(/* turbopackIgnore: true */ process.cwd(), "content", "maps");

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
  return path.join(DATA_DIR, fileName);
}

export function resolveMapDownloadPath(): string {
  return path.join(MAPS_DIR, MAP_FILE_NAME);
}

export function contentDataDir(): string {
  return DATA_DIR;
}
