"use client";

import { useSetting } from "@/hooks/useSetting";
import { RadioGroup } from "../RadioGroup";
import { SORT_FIELD_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "default_sort_field";
const DEFAULT_VALUE = "timestamp";

/**
 * Default sort field configuration component.
 *
 * Manages the default field to sort books by.
 * Follows SRP by handling only sort field preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function DefaultSortFieldConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Default Sort Field"
      options={[...SORT_FIELD_OPTIONS]}
      value={value}
      onChange={setValue}
      name="default-sort-field"
    />
  );
}
