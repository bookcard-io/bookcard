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
import { PAGE_SIZE_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "default_page_size";
const DEFAULT_VALUE = "20";

/**
 * Default page size configuration component.
 *
 * Manages the number of books displayed per page.
 * Follows SRP by handling only page size preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function DefaultPageSizeConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Books Per Page"
      options={[...PAGE_SIZE_OPTIONS]}
      value={value}
      onChange={setValue}
      name="default-page-size"
    />
  );
}
