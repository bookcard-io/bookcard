"use client";

import { useBlurAfterClick } from "./BlurAfterClickContext";
import { ToggleButton } from "./ToggleButton";

interface RadioButtonGroupProps {
  /**
   * Label for the group.
   */
  label: string;
  /**
   * Available options to display as toggle buttons.
   */
  options: string[];
  /**
   * Currently selected option (single value).
   */
  selected: string;
  /**
   * Callback fired when an option is selected.
   */
  onSelect: (option: string) => void;
}

/**
 * Radio button group styled as pills for single-select options.
 *
 * Displays a group of toggle buttons styled as pills, but enforces single selection
 * (radio behavior). Follows SRP by handling only group layout and delegation.
 * Follows IOC by accepting callbacks for selection events.
 *
 * Parameters
 * ----------
 * label : string
 *     Label for the group.
 * options : string[]
 *     Available options to display.
 * selected : string
 *     Currently selected option.
 * onSelect : (option: string) => void
 *     Callback fired when an option is selected.
 */
export function RadioButtonGroup({
  label,
  options,
  selected,
  onSelect,
}: RadioButtonGroupProps) {
  const { onBlurClick } = useBlurAfterClick();

  return (
    <div className="flex flex-col gap-3">
      <div className="font-medium text-sm text-text-a20">{label}</div>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <ToggleButton
            key={option}
            label={option}
            isSelected={selected === option}
            onClick={onBlurClick(() => onSelect(option))}
          />
        ))}
      </div>
    </div>
  );
}
