"use client";

import { useSetting } from "@/hooks/useSetting";
import { RadioGroup } from "../RadioGroup";
import { DISPLAY_MODE_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "books_grid_display";
const DEFAULT_VALUE = "pagination";

/**
 * Display mode configuration component.
 *
 * Manages books grid display preference (pagination vs infinite scroll).
 * Follows SRP by handling only display mode preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function DisplayModeConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Books Grid Display"
      options={[...DISPLAY_MODE_OPTIONS]}
      value={value}
      onChange={setValue}
      name="display-mode"
    />
  );
}
