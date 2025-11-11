"use client";

import { ToggleButton } from "./ToggleButton";

interface ToggleButtonGroupProps {
  /**
   * Label for the group.
   */
  label: string;
  /**
   * Available options to display as toggle buttons.
   */
  options: string[];
  /**
   * Currently selected options.
   */
  selected: string[];
  /**
   * Callback fired when an option is toggled.
   */
  onToggle: (option: string) => void;
}

/**
 * Toggle button group component.
 *
 * Displays a group of toggle buttons for multi-select options.
 * Follows SRP by handling only group layout and delegation to ToggleButton.
 * Follows IOC by accepting callbacks for toggle events.
 *
 * Parameters
 * ----------
 * label : string
 *     Label for the group.
 * options : string[]
 *     Available options to display.
 * selected : string[]
 *     Currently selected options.
 * onToggle : (option: string) => void
 *     Callback fired when an option is toggled.
 */
export function ToggleButtonGroup({
  label,
  options,
  selected,
  onToggle,
}: ToggleButtonGroupProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="font-medium text-sm text-text-a20">{label}</div>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <ToggleButton
            key={option}
            label={option}
            isSelected={selected.includes(option)}
            onClick={() => onToggle(option)}
          />
        ))}
      </div>
    </div>
  );
}
