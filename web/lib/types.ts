export type CsvDataset = {
  id: string;
  label: string;
  fileName: string;
  headers: string[];
  rows: string[][];
};

export type PrecinctAssignment = {
  precinct: string;
  assignedVspc: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  distanceMiles: string;
};
