"use client";

import { useState } from "react";
import { RadioGroup } from "../RadioGroup";
import { PAGE_SIZE_OPTIONS } from "./configurationConstants";

/**
 * Default page size configuration component.
 *
 * Manages the number of books displayed per page.
 * Follows SRP by handling only page size preference.
 */
export function DefaultPageSizeConfiguration() {
  const [pageSize, setPageSize] = useState("20");

  return (
    <RadioGroup
      label="Books Per Page"
      options={[...PAGE_SIZE_OPTIONS]}
      value={pageSize}
      onChange={(value) => {
        setPageSize(value);
      }}
      name="default-page-size"
    />
  );
}
