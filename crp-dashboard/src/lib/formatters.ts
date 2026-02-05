export function formatBps(value: number): string {
  return `${Math.round(value)} bps`;
}

export function formatPercent(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function formatMillions(value: number, decimals = 0): string {
  return `$${value.toFixed(decimals)}M`;
}

export function formatCurrency(value: number): string {
  if (Math.abs(value) >= 1e9) {
    return `$${(value / 1e9).toFixed(1)}B`;
  }
  if (Math.abs(value) >= 1e6) {
    return `$${(value / 1e6).toFixed(0)}M`;
  }
  return `$${(value / 1e3).toFixed(0)}K`;
}

export function formatDscr(value: number): string {
  return `${value.toFixed(2)}x`;
}

export function formatRating(rating: string): string {
  return rating;
}

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(" ");
}
