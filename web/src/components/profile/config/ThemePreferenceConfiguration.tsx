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
import {
  THEME_PREFERENCE_OPTIONS,
  THEME_PREFERENCE_SETTING_KEY,
} from "./configurationConstants";

const DEFAULT_VALUE = "dark";

/**
 * Theme preference configuration component.
 *
 * Manages theme preference (dark vs light).
 * Follows SRP by handling only theme preference.
 * Follows IOC by using useSetting hook for persistence.
 * Theme changes are automatically applied by useTheme hook which watches
 * the setting value.
 */
export function ThemePreferenceConfiguration() {
  const { value, setValue } = useSetting({
    key: THEME_PREFERENCE_SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Theme Preference"
      options={[...THEME_PREFERENCE_OPTIONS]}
      value={value}
      onChange={setValue}
      name="theme-preference"
    />
  );
}
