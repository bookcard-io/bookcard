"use client";

import { useMultiSelect } from "@/hooks/useMultiSelect";
import { ToggleButtonGroup } from "../ToggleButtonGroup";
import { AVAILABLE_METADATA_PROVIDERS } from "./configurationConstants";

/**
 * Metadata providers configuration component.
 *
 * Manages preferred metadata providers selection.
 * Follows SRP by handling only metadata provider preferences.
 * Follows IOC by using useMultiSelect hook.
 */
export function MetadataProvidersConfiguration() {
  const { selected, toggle } = useMultiSelect<string>({
    initialSelected: [],
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
