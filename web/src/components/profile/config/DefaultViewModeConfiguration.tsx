"use client";

import { useState } from "react";
import { RadioGroup } from "../RadioGroup";
import { VIEW_MODE_OPTIONS } from "./configurationConstants";

/**
 * Default view mode configuration component.
 *
 * Manages the default view mode (grid vs list).
 * Follows SRP by handling only view mode preference.
 */
export function DefaultViewModeConfiguration() {
  const [viewMode, setViewMode] = useState("grid");

  return (
    <RadioGroup
      label="Default View Mode"
      options={[...VIEW_MODE_OPTIONS]}
      value={viewMode}
      onChange={(value) => {
        setViewMode(value);
      }}
      name="default-view-mode"
    />
  );
}
