/**
 * Single library statistic pill component.
 *
 * Renders a single pill badge for a statistic.
 * Follows SRP by focusing solely on individual pill rendering.
 */

export interface LibraryStatPillProps {
  /** Formatted value to display. */
  value: string;
  /** Label to display (e.g., "BOOKS"). */
  label: string;
}

/**
 * Library statistic pill component.
 *
 * Renders a single rounded pill badge with value and label.
 *
 * Parameters
 * ----------
 * props : LibraryStatPillProps
 *     Component props including value and label.
 */
export function LibraryStatPill({ value, label }: LibraryStatPillProps) {
  return (
    <div className="rounded-full bg-[var(--color-info-a20)] px-2.5 py-1 font-medium text-gray-900 text-xs">
      {value} {label}
    </div>
  );
}
