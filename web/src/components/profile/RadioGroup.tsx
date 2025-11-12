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

interface RadioOption {
  /**
   * Option value.
   */
  value: string;
  /**
   * Option label.
   */
  label: string;
}

interface RadioGroupProps {
  /**
   * Label for the radio group.
   */
  label: string;
  /**
   * Available radio options.
   */
  options: RadioOption[];
  /**
   * Currently selected value.
   */
  value: string;
  /**
   * Callback fired when selection changes.
   */
  onChange: (value: string) => void;
  /**
   * Name attribute for radio inputs (for grouping).
   */
  name: string;
}

/**
 * Radio group component for single-select options.
 *
 * Displays a group of radio buttons for selecting one option.
 * Follows SRP by handling only radio group UI and selection.
 * Follows IOC by accepting callbacks for change events.
 *
 * Parameters
 * ----------
 * label : string
 *     Label for the radio group.
 * options : RadioOption[]
 *     Available radio options.
 * value : string
 *     Currently selected value.
 * onChange : (value: string) => void
 *     Callback fired when selection changes.
 * name : string
 *     Name attribute for radio inputs.
 */
export function RadioGroup({
  label,
  options,
  value,
  onChange,
  name,
}: RadioGroupProps) {
  const { onBlurChange } = useBlurAfterClick();

  return (
    <div className="flex flex-col gap-3">
      <div className="font-medium text-sm text-text-a20">{label}</div>
      <div className="flex gap-4">
        {options.map((option) => (
          <label
            key={option.value}
            className="flex cursor-pointer items-center gap-2"
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={onBlurChange(() => onChange(option.value))}
              className="h-4 w-4 text-primary-a0 focus:ring-2 focus:ring-primary-a0"
            />
            <span className="text-text-a0">{option.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
