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

import { useSetting } from "@/hooks/useSetting";
import { RadioGroup } from "../RadioGroup";
import { DISPLAY_MODE_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "books_grid_display";
const DEFAULT_VALUE = "pagination";

/**
 * Display mode configuration component.
 *
 * Manages books grid display preference (pagination vs infinite scroll).
 * Follows SRP by handling only display mode preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function DisplayModeConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Books Grid Display"
      options={[...DISPLAY_MODE_OPTIONS]}
      value={value}
      onChange={setValue}
      name="display-mode"
    />
  );
}
