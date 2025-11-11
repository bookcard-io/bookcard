"use client";

import { cn } from "@/libs/utils";

interface ToggleButtonProps {
  /**
   * Button label text.
   */
  label: string;
  /**
   * Whether the button is currently selected/active.
   */
  isSelected: boolean;
  /**
   * Callback fired when button is clicked.
   */
  onClick: (e: React.MouseEvent<HTMLButtonElement>) => void;
}

/**
 * Toggle button component for multi-select options.
 *
 * Displays a button that can be toggled on/off.
 * Follows SRP by handling only button UI and click events.
 *
 * Parameters
 * ----------
 * label : string
 *     Button label text.
 * isSelected : boolean
 *     Whether the button is currently selected.
 * onClick : (e: React.MouseEvent<HTMLButtonElement>) => void
 *     Callback fired when button is clicked.
 */
export function ToggleButton({
  label,
  isSelected,
  onClick,
}: ToggleButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded border px-3 py-1.5 font-medium text-sm transition-colors duration-200",
        isSelected
          ? "border-primary-a0 bg-primary-a0 text-text-a0"
          : "border-surface-a20 bg-surface-tonal-a10 text-text-a0 hover:bg-surface-tonal-a20",
      )}
      aria-pressed={isSelected}
    >
      {label}
    </button>
  );
}
