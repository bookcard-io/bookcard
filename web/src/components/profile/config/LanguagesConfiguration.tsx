// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

"use client";

import { useEffect, useState } from "react";
import { useSettings } from "@/contexts/SettingsContext";
import { RadioButtonGroup } from "../RadioButtonGroup";

const SETTING_KEY = "preferred_language";
const DEFAULT_ISO_CODE = "en"; // English

// Top 12 most popular languages by global usage
const TOP_LANGUAGES: Array<{ baseCode: string; name: string }> = [
  { baseCode: "en", name: "English" },
  { baseCode: "zh", name: "Chinese (Simplified)" },
  { baseCode: "es", name: "Spanish (Spain)" },
  { baseCode: "hi", name: "Hindi" },
  { baseCode: "ar", name: "Arabic" },
  { baseCode: "pt", name: "Portuguese" },
  { baseCode: "bn", name: "Bengali" },
  { baseCode: "ru", name: "Russian" },
  { baseCode: "ja", name: "Japanese" },
  { baseCode: "de", name: "German" },
  { baseCode: "fr", name: "French" },
  { baseCode: "ko", name: "Korean" },
];

// Create mapping: ISO code -> Friendly name
const ISO_TO_NAME = new Map(
  TOP_LANGUAGES.map((lang) => [lang.baseCode, lang.name]),
);
// Create reverse mapping: Friendly name -> ISO code
const NAME_TO_ISO = new Map(
  TOP_LANGUAGES.map((lang) => [lang.name, lang.baseCode]),
);
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
