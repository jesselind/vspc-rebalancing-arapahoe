/** Dataset ids from `web/tools/generate-home-data.mjs` — keep in sync. */
export const VSPC_LOCATIONS_DATASET_ID = "vspc-locations";
export const PRECINCT_DISTRIBUTION_DATASET_ID = "vspc-precinct-distribution";

/** CSV column headers (data files unchanged; display may differ). */
export const PRECINCT_MAP_URL_HEADER = "Precinct Map URL";
export const ASSIGNED_VSPC_HEADER = "Assigned VSPC";
export const ADDRESS_HEADER = "Address";

export const PROPORTION_PERCENT_HEADERS = new Set([
  "Primary DC % of Precincts",
  "Secondary DC % of Precincts",
]);

export const VSPC_MAP_LINK_HEADERS = new Set(["Nearest VSPC", ASSIGNED_VSPC_HEADER]);
