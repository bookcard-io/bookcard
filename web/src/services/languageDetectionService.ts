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

import { type LanguageEntry, POPULAR_LANGUAGES } from "@/constants/languages";

const LANGUAGE_ABBREVIATIONS: Record<string, string> = {
  ENG: "English",
  SPA: "Spanish",
  FRE: "French",
  GER: "German",
  ITA: "Italian",
  POR: "Portuguese",
  RUS: "Russian",
  JPN: "Japanese",
  CHI: "Chinese",
  KOR: "Korean",
  ARA: "Arabic",
  HIN: "Hindi",
  BEN: "Bengali",
  TUR: "Turkish",
  VIE: "Vietnamese",
};

export class LanguageDetectionService {
  constructor(
    private abbreviations: Record<string, string>,
    private languages: LanguageEntry[],
  ) {}

  detect(title: string): LanguageEntry {
    return (
      this.detectByAbbreviation(title) ||
      this.detectByLanguageName(title) ||
      this.detectByISOCode(title) ||
      this.getUnknown()
    );
  }

  private detectByAbbreviation(title: string): LanguageEntry | null {
    for (const [abbr, langName] of Object.entries(this.abbreviations)) {
      if (new RegExp(`\\b${abbr}\\b`, "i").test(title)) {
        return (
          this.languages.find(
            (l) => l.englishName === langName && !l.code.includes("-"),
          ) ||
          this.languages.find((l) => l.englishName === langName) ||
          null
        );
      }
    }
    return null;
  }

  private detectByLanguageName(title: string): LanguageEntry | null {
    for (const lang of this.languages) {
      // Check English Name
      if (new RegExp(`\\b${lang.englishName}\\b`, "i").test(title)) {
        return lang;
      }

      // Check Native Name (if different)
      if (
        lang.name !== lang.englishName &&
        title.toLowerCase().includes(lang.name.toLowerCase())
      ) {
        return lang;
      }
    }
    return null;
  }

  private detectByISOCode(title: string): LanguageEntry | null {
    for (const lang of this.languages) {
      // Check ISO Code
      // We need to be careful with 2-letter codes that are common words
      const code = lang.code;
      const baseCode = code.split("-")[0] ?? "";
      const isCommonWord = [
        "IT",
        "IS",
        "NO",
        "HE",
        "ME",
        "MY",
        "WE",
        "US",
        "IN",
        "ON",
        "OR",
        "AT",
        "BE",
        "BY",
        "AS",
        "ID",
        "UP",
        "AM",
        "PM",
        "DO",
        "GO",
        "SO",
        "TO",
        "IF",
        "OF",
        "AN",
      ].includes(baseCode.toUpperCase());

      if (isCommonWord) {
        // stricter check for common words: [IT], (IT)
        if (new RegExp(`[\\[\\(]${code}[\\]\\)]`, "i").test(title)) {
          return lang;
        }
      } else {
        // standard check for other codes: word boundary or separators
        if (new RegExp(`\\b${code}\\b`, "i").test(title)) {
          return lang;
        }
      }
    }
    return null;
  }

  private getUnknown(): LanguageEntry {
    return {
      code: "un",
      name: "Unknown",
      flag: "🇺🇳",
      englishName: "Unknown",
    };
  }
}

export const languageDetector = new LanguageDetectionService(
  LANGUAGE_ABBREVIATIONS,
  POPULAR_LANGUAGES,
);
