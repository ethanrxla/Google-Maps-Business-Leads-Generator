export const LEAD_PACK_SIZES = [20, 100, 500, 1000] as const;

export const LEAD_PACK_PRICES: Record<number, number> = {
  20: 12,
  100: 40,
  500: 250,
  1000: 400,
};

export function formatLeadOption(size: number) {
  const price = LEAD_PACK_PRICES[size];
  return price ? `${size} leads — $${price}` : `${size} leads`;
}
