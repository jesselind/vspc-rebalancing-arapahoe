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
