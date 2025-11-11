"use client";

import { useState } from "react";
import { RadioGroup } from "../RadioGroup";
import { DISPLAY_MODE_OPTIONS } from "./configurationConstants";

/**
 * Display mode configuration component.
 *
 * Manages books grid display preference (pagination vs infinite scroll).
 * Follows SRP by handling only display mode preference.
 */
export function DisplayModeConfiguration() {
  const [displayMode, setDisplayMode] = useState("pagination");

  return (
    <RadioGroup
      label="Books Grid Display"
      options={[...DISPLAY_MODE_OPTIONS]}
      value={displayMode}
      onChange={setDisplayMode}
      name="display-mode"
    />
  );
}
