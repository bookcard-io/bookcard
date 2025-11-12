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
  const { onBlurClick } = useBlurAfterClick();

  return (
    <div className="flex flex-col gap-3">
      <div className="font-medium text-sm text-text-a20">{label}</div>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <ToggleButton
            key={option}
            label={option}
            isSelected={selected.includes(option)}
            onClick={onBlurClick(() => onToggle(option))}
          />
        ))}
      </div>
    </div>
  );
}
