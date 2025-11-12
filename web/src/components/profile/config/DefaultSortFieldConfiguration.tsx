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
import { SORT_FIELD_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "default_sort_field";
const DEFAULT_VALUE = "timestamp";

/**
 * Default sort field configuration component.
 *
 * Manages the default field to sort books by.
 * Follows SRP by handling only sort field preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function DefaultSortFieldConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Default Sort Field"
      options={[...SORT_FIELD_OPTIONS]}
      value={value}
      onChange={setValue}
      name="default-sort-field"
    />
  );
}
