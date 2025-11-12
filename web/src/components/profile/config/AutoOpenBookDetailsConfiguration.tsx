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
import { BOOK_DETAILS_OPEN_MODE_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "book_details_open_mode";
const DEFAULT_VALUE = "modal";

/**
 * Auto-open book details configuration component.
 *
 * Manages how book details are opened (modal vs page navigation).
 * Follows SRP by handling only book details open mode preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function AutoOpenBookDetailsConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Book Details Open Mode"
      options={[...BOOK_DETAILS_OPEN_MODE_OPTIONS]}
      value={value}
      onChange={setValue}
      name="book-details-open-mode"
    />
  );
}
