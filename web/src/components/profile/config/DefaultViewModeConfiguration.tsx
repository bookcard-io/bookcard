"use client";

import { useSetting } from "@/hooks/useSetting";
import { RadioGroup } from "../RadioGroup";
import { VIEW_MODE_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "default_view_mode";
const DEFAULT_VALUE = "grid";

/**
 * Default view mode configuration component.
 *
 * Manages the default view mode (grid vs list).
 * Follows SRP by handling only view mode preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function DefaultViewModeConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Default View Mode"
      options={[...VIEW_MODE_OPTIONS]}
      value={value}
      onChange={setValue}
      name="default-view-mode"
    />
  );
}
