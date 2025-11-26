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

import { useArraySetting } from "@/hooks/useArraySetting";
import { useMultiSelect } from "@/hooks/useMultiSelect";
import { ToggleButtonGroup } from "../ToggleButtonGroup";
import {
  AVAILABLE_METADATA_PROVIDERS,
  DEFAULT_ENABLED_METADATA_PROVIDERS,
  ENABLED_METADATA_PROVIDERS_SETTING_KEY,
} from "./configurationConstants";

/**
 * Enabled metadata providers configuration component.
 *
 * Manages which metadata providers are enabled and visible in the metadata fetch modal.
 * A provider must be enabled to show up in the list of provider statuses.
 * Follows SRP by handling only enabled provider visibility preferences.
 * Follows IOC by using useMultiSelect and useArraySetting hooks for persistence.
 */
export function EnabledMetadataProvidersConfiguration() {
  const { selected, toggle, setSelected } = useMultiSelect<string>({
    initialSelected: [...DEFAULT_ENABLED_METADATA_PROVIDERS],
  });

  // Handle loading and saving array setting
  useArraySetting({
    key: ENABLED_METADATA_PROVIDERS_SETTING_KEY,
    defaultValue: [...DEFAULT_ENABLED_METADATA_PROVIDERS],
    value: selected,
    setValue: setSelected,
  });

  return (
    <ToggleButtonGroup
      label="Enabled Metadata Providers"
      options={[...AVAILABLE_METADATA_PROVIDERS]}
      selected={selected}
      onToggle={toggle}
    />
  );
}
