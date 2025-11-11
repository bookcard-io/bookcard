"use client";

import { useState } from "react";
import { RadioGroup } from "../RadioGroup";
import { BOOK_DETAILS_OPEN_MODE_OPTIONS } from "./configurationConstants";

/**
 * Auto-open book details configuration component.
 *
 * Manages how book details are opened (modal vs page navigation).
 * Follows SRP by handling only book details open mode preference.
 */
export function AutoOpenBookDetailsConfiguration() {
  const [openMode, setOpenMode] = useState("modal");

  return (
    <RadioGroup
      label="Book Details Open Mode"
      options={[...BOOK_DETAILS_OPEN_MODE_OPTIONS]}
      value={openMode}
      onChange={(value) => {
        setOpenMode(value);
      }}
      name="book-details-open-mode"
    />
  );
}
