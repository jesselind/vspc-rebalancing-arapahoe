/** Dataset ids from `web/tools/generate-home-data.mjs` — keep in sync. */
export const VSPC_LOCATIONS_DATASET_ID = "vspc-locations";
export const PRECINCT_DISTRIBUTION_DATASET_ID = "vspc-precinct-distribution";
export const DC_ASSIGNMENT_VERIFICATION_DATASET_ID = "dc-assignment-verification";
export const SUMMARY_STATISTICS_DATASET_ID = "summary-statistics";

/** Short context shown above each report table in the Reports section. */
export const REPORT_DESCRIPTIONS: Record<string, string> = {
  [VSPC_LOCATIONS_DATASET_ID]:
    "Master list of VSPCs showing number of assigned voters and precincts.",
  [PRECINCT_DISTRIBUTION_DATASET_ID]:
    "Nearest vs. assigned VSPC, distances, and whether the precinct was reassigned.",
  [DC_ASSIGNMENT_VERIFICATION_DATASET_ID]:
    "Which Captain Districts are assigned to each VSPC, based on the share of that DC's precincts at the location.",
  [SUMMARY_STATISTICS_DATASET_ID]:
    "Total VSPCs, precincts, and reassignments from the nearest VSPC.",
};

/** CSV column headers (data files unchanged; display may differ). */
export const PRECINCT_MAP_URL_HEADER = "Precinct Map URL";
export const ASSIGNED_VSPC_HEADER = "Assigned VSPC";
export const ADDRESS_HEADER = "Address";

export const PROPORTION_PERCENT_HEADERS = new Set([
  "Primary DC % of Precincts",
  "Secondary DC % of Precincts",
]);

export const VSPC_MAP_LINK_HEADERS = new Set(["Nearest VSPC", ASSIGNED_VSPC_HEADER]);
