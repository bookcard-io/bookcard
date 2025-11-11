"use client";

import { useSetting } from "@/hooks/useSetting";
import { RadioGroup } from "../RadioGroup";
import { SORT_ORDER_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "default_sort_order";
const DEFAULT_VALUE = "desc";

/**
 * Default sort order configuration component.
 *
 * Manages the default sort order (ascending/descending).
 * Follows SRP by handling only sort order preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function DefaultSortOrderConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Default Sort Order"
      options={[...SORT_ORDER_OPTIONS]}
      value={value}
      onChange={setValue}
      name="default-sort-order"
    />
  );
}
