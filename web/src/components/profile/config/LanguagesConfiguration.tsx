"use client";

import { useState } from "react";
import { RadioButtonGroup } from "../RadioButtonGroup";
import { AVAILABLE_LANGUAGES } from "./configurationConstants";

/**
 * Languages configuration component.
 *
 * Manages preferred language selection (single select with pill styling).
 * Follows SRP by handling only language preference.
 */
export function LanguagesConfiguration() {
  const [selectedLanguage, setSelectedLanguage] = useState("English");

  return (
    <RadioButtonGroup
      label="Preferred Language"
      options={[...AVAILABLE_LANGUAGES]}
      selected={selectedLanguage}
      onSelect={setSelectedLanguage}
    />
  );
}
