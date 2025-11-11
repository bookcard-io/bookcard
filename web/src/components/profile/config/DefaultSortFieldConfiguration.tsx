"use client";

import { useState } from "react";
import { RadioGroup } from "../RadioGroup";
import { SORT_FIELD_OPTIONS } from "./configurationConstants";

/**
 * Default sort field configuration component.
 *
 * Manages the default field to sort books by.
 * Follows SRP by handling only sort field preference.
 */
export function DefaultSortFieldConfiguration() {
  const [sortField, setSortField] = useState("timestamp");

  return (
    <RadioGroup
      label="Default Sort Field"
      options={[...SORT_FIELD_OPTIONS]}
      value={sortField}
      onChange={(value) => {
        setSortField(value);
      }}
      name="default-sort-field"
    />
  );
}
