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

import { useEffect, useState } from "react";
import { useSettings } from "@/contexts/SettingsContext";

export interface UseBooleanSettingOptions {
  /**
   * Setting key to load and save.
   */
  key: string;
  /**
   * Default value if setting is not found.
   */
  defaultValue: boolean;
}

export interface UseBooleanSettingResult {
  /**
   * Current setting value.
   */
  value: boolean;
  /**
   * Update the setting value.
   */
  setValue: (value: boolean) => void;
  /**
   * Whether settings are currently loading.
   */
  isLoading: boolean;
}

/**
 * Custom hook for managing a boolean setting.
 *
 * Handles conversion between boolean and string ("true"/"false").
 * Follows DRY by eliminating code duplication for boolean settings.
 * Follows SRP by handling only boolean setting state management.
 * Follows IOC by using settings context for persistence.
 *
 * Parameters
 * ----------
 * options : UseBooleanSettingOptions
 *     Configuration including setting key and default value.
 *
 * Returns
 * -------
 * UseBooleanSettingResult
 *     Setting value, update function, and loading state.
 */
export function useBooleanSetting({
  key,
  defaultValue,
}: UseBooleanSettingOptions): UseBooleanSettingResult {
  const { getSetting, updateSetting, isLoading } = useSettings();
  const [value, setValue] = useState(defaultValue);

  // Load setting value on mount or when settings are loaded
  useEffect(() => {
    if (!isLoading) {
      const savedValue = getSetting(key);
      if (savedValue !== null) {
        setValue(savedValue === "true");
      }
    }
  }, [getSetting, isLoading, key]);

  const handleSetValue = (newValue: boolean) => {
    setValue(newValue);
    updateSetting(key, newValue ? "true" : "false");
  };

  return {
    value,
    setValue: handleSetValue,
    isLoading,
  };
}
