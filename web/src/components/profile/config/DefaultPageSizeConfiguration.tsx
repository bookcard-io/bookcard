"use client";

import { useSetting } from "@/hooks/useSetting";
import { RadioGroup } from "../RadioGroup";
import { PAGE_SIZE_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "default_page_size";
const DEFAULT_VALUE = "20";

/**
 * Default page size configuration component.
 *
 * Manages the number of books displayed per page.
 * Follows SRP by handling only page size preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function DefaultPageSizeConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Books Per Page"
      options={[...PAGE_SIZE_OPTIONS]}
      value={value}
      onChange={setValue}
      name="default-page-size"
    />
  );
}
