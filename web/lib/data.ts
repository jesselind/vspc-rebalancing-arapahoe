import type { CsvDataset, PrecinctAssignment } from "./types";
import { datasets, precinctAssignments } from "./generated/home-data";

export async function loadDatasets(): Promise<CsvDataset[]> {
  return datasets;
}

export async function loadPrecinctAssignments(): Promise<Map<string, PrecinctAssignment>> {
  return new Map(precinctAssignments.map((assignment) => [assignment.precinct, assignment]));
}
