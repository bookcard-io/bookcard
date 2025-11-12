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

export interface UseSettingOptions {
  /**
   * Setting key to load and save.
   */
  key: string;
  /**
   * Default value if setting is not found.
   */
  defaultValue: string;
}

export interface UseSettingResult {
  /**
   * Current setting value.
   */
  value: string;
  /**
   * Update the setting value.
   */
  setValue: (value: string) => void;
  /**
   * Whether settings are currently loading.
   */
  isLoading: boolean;
}

/**
 * Custom hook for managing a single setting.
 *
 * Encapsulates the common pattern of loading and saving a setting.
 * Follows DRY by eliminating code duplication across config components.
 * Follows SRP by handling only single-setting state management.
 * Follows IOC by using settings context for persistence.
 *
 * Parameters
 * ----------
 * options : UseSettingOptions
 *     Configuration including setting key and default value.
 *
 * Returns
 * -------
 * UseSettingResult
 *     Setting value, update function, and loading state.
 */
export function useSetting({
  key,
  defaultValue,
}: UseSettingOptions): UseSettingResult {
  const { getSetting, updateSetting, isLoading } = useSettings();
  const [value, setValue] = useState(defaultValue);

  // Load setting value on mount or when settings are loaded
  useEffect(() => {
    if (!isLoading) {
      const savedValue = getSetting(key);
      if (savedValue) {
        setValue(savedValue);
      }
    }
  }, [getSetting, isLoading, key]);

  const handleSetValue = (newValue: string) => {
    setValue(newValue);
    updateSetting(key, newValue);
  };

  return {
    value,
    setValue: handleSetValue,
    isLoading,
  };
}
