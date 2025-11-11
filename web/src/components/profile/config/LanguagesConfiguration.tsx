"use client";

import { useEffect, useState } from "react";
import { POPULAR_LANGUAGES } from "@/constants/languages";
import { useSettings } from "@/contexts/SettingsContext";
import { RadioButtonGroup } from "../RadioButtonGroup";

const SETTING_KEY = "preferred_language";
const DEFAULT_ISO_CODE = "en"; // English

// Top 12 languages from POPULAR_LANGUAGES
const TOP_LANGUAGES = POPULAR_LANGUAGES.slice(0, 12);

// Create mapping: ISO code -> Friendly name
const ISO_TO_NAME = new Map(TOP_LANGUAGES);
// Create reverse mapping: Friendly name -> ISO code
const NAME_TO_ISO = new Map(TOP_LANGUAGES.map(([iso, name]) => [name, iso]));
// Array of friendly names for display
const LANGUAGE_NAMES = Array.from(ISO_TO_NAME.values());

/**
 * Languages configuration component.
 *
 * Manages preferred language selection (single select with pill styling).
 * Displays friendly names but stores ISO 639-1 codes in the backend.
 * Follows SRP by handling only language preference.
 * Follows IOC by using settings context for persistence.
 */
export function LanguagesConfiguration() {
  const { getSetting, updateSetting, isLoading } = useSettings();
  const [selectedLanguageName, setSelectedLanguageName] = useState(
    ISO_TO_NAME.get(DEFAULT_ISO_CODE) || "English",
  );

  // Load setting value on mount or when settings are loaded
  useEffect(() => {
    if (!isLoading) {
      const savedIsoCode = getSetting(SETTING_KEY);
      if (savedIsoCode) {
        const languageName = ISO_TO_NAME.get(savedIsoCode);
        if (languageName) {
          setSelectedLanguageName(languageName);
        }
      }
    }
  }, [getSetting, isLoading]);

  const handleSelect = (languageName: string) => {
    setSelectedLanguageName(languageName);
    const isoCode = NAME_TO_ISO.get(languageName);
    if (isoCode) {
      updateSetting(SETTING_KEY, isoCode);
    }
  };

  return (
    <RadioButtonGroup
      label="Preferred Language"
      options={LANGUAGE_NAMES}
      selected={selectedLanguageName}
      onSelect={handleSelect}
    />
  );
}
