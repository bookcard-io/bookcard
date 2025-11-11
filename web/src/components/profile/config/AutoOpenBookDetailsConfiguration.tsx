"use client";

import { useSetting } from "@/hooks/useSetting";
import { RadioGroup } from "../RadioGroup";
import { BOOK_DETAILS_OPEN_MODE_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "book_details_open_mode";
const DEFAULT_VALUE = "modal";

/**
 * Auto-open book details configuration component.
 *
 * Manages how book details are opened (modal vs page navigation).
 * Follows SRP by handling only book details open mode preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function AutoOpenBookDetailsConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Book Details Open Mode"
      options={[...BOOK_DETAILS_OPEN_MODE_OPTIONS]}
      value={value}
      onChange={setValue}
      name="book-details-open-mode"
    />
  );
}
