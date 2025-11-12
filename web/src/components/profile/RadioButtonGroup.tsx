// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
