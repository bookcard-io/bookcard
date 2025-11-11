"use client";

import { useArraySetting } from "@/hooks/useArraySetting";
import { useMultiSelect } from "@/hooks/useMultiSelect";
import { ToggleButtonGroup } from "../ToggleButtonGroup";
import { AVAILABLE_METADATA_PROVIDERS } from "./configurationConstants";

const SETTING_KEY = "preferred_metadata_providers";
const DEFAULT_VALUE: string[] = [];

/**
 * Metadata providers configuration component.
 *
 * Manages preferred metadata providers selection.
 * Follows SRP by handling only metadata provider preferences.
 * Follows IOC by using useMultiSelect and useArraySetting hooks for persistence.
 */
export function MetadataProvidersConfiguration() {
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
      label="Preferred Metadata Providers"
      options={[...AVAILABLE_METADATA_PROVIDERS]}
      selected={selected}
      onToggle={toggle}
    />
  );
}
