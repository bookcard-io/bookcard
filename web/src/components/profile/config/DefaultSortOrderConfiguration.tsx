"use client";

import { useState } from "react";
import { RadioGroup } from "../RadioGroup";
import { SORT_ORDER_OPTIONS } from "./configurationConstants";

/**
 * Default sort order configuration component.
 *
 * Manages the default sort order (ascending/descending).
 * Follows SRP by handling only sort order preference.
 */
export function DefaultSortOrderConfiguration() {
  const [sortOrder, setSortOrder] = useState("desc");

  return (
    <RadioGroup
      label="Default Sort Order"
      options={[...SORT_ORDER_OPTIONS]}
      value={sortOrder}
      onChange={(value) => {
        setSortOrder(value);
      }}
      name="default-sort-order"
    />
  );
}
