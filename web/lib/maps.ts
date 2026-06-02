import { ADDRESS_HEADER, ASSIGNED_VSPC_HEADER } from "@/lib/csv-reports";

type AddressParts = {
  address: string;
  city: string;
  state: string;
  zip: string;
};

export function formatFullAddress({ address, city, state, zip }: AddressParts): string {
  const stateZip = [state, zip].filter(Boolean).join(" ");
  return [address, city, stateZip].filter((part) => part.trim().length > 0).join(", ");
}

/** Opens search in Google Maps (browser or app on mobile). */
export function googleMapsSearchUrl(fullAddress: string): string {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(fullAddress)}`;
}

export const googleMapsLinkClass =
  "font-medium text-blue-700 underline decoration-blue-400 underline-offset-2 hover:text-blue-900";

export function vspcLocationMapsUrlFromRow(headers: string[], row: string[]): string | null {
  const addressIndex = headers.indexOf(ADDRESS_HEADER);
  if (addressIndex < 0) {
    return null;
  }

  const address = row[addressIndex]?.trim() ?? "";
  if (!address) {
    return null;
  }

  const cityIndex = headers.indexOf("City");
  const stateIndex = headers.indexOf("State");
  const zipIndex = headers.findIndex((header) => header === "ZIP" || header === "Zip");

  const fullAddress = formatFullAddress({
    address,
    city: cityIndex >= 0 ? (row[cityIndex] ?? "") : "",
    state: stateIndex >= 0 ? (row[stateIndex] ?? "") : "",
    zip: zipIndex >= 0 ? (row[zipIndex] ?? "") : "",
  });

  return fullAddress ? googleMapsSearchUrl(fullAddress) : null;
}

export type VspcMapsLookup = ReadonlyMap<string, string>;

export function buildVspcMapsLookup(headers: string[], rows: string[][]): VspcMapsLookup {
  const assignedIndex = headers.indexOf(ASSIGNED_VSPC_HEADER);
  if (assignedIndex < 0) {
    return new Map();
  }

  const lookup = new Map<string, string>();
  for (const row of rows) {
    const name = row[assignedIndex]?.trim();
    if (!name || lookup.has(name)) {
      continue;
    }

    const mapsUrl = vspcLocationMapsUrlFromRow(headers, row);
    if (mapsUrl) {
      lookup.set(name, mapsUrl);
    }
  }

  return lookup;
}

export function vspcNameMapsUrl(vspcName: string, lookup?: VspcMapsLookup): string | null {
  const trimmed = vspcName.trim();
  if (!trimmed) {
    return null;
  }

  return lookup?.get(trimmed) ?? googleMapsSearchUrl(trimmed);
}
