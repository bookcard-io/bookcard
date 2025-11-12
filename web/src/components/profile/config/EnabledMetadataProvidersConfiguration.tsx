"use client";

import { useArraySetting } from "@/hooks/useArraySetting";
import { useMultiSelect } from "@/hooks/useMultiSelect";
import { ToggleButtonGroup } from "../ToggleButtonGroup";
import { AVAILABLE_METADATA_PROVIDERS } from "./configurationConstants";

const SETTING_KEY = "enabled_metadata_providers";
const DEFAULT_VALUE: string[] = ["Google Books", "Amazon"];

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
    initialSelected: DEFAULT_VALUE,
  });

  // Handle loading and saving array setting
  useArraySetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
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
