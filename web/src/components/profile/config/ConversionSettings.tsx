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

import { useEffect, useRef, useState } from "react";
import { useSettings } from "@/contexts/SettingsContext";
import { useBooleanSetting } from "@/hooks/useBooleanSetting";
import { useSetting } from "@/hooks/useSetting";
import { useBlurAfterClick } from "../BlurAfterClickContext";
import { RadioGroup } from "../RadioGroup";
import {
  AUTO_CONVERT_BACKUP_ORIGINALS_SETTING_KEY,
  AUTO_CONVERT_IGNORED_FORMATS_SETTING_KEY,
  AUTO_CONVERT_ON_IMPORT_SETTING_KEY,
  AUTO_CONVERT_TARGET_FORMAT_SETTING_KEY,
  CONVERSION_TARGET_FORMAT_OPTIONS,
  SUPPORTED_BOOK_FORMATS,
} from "./configurationConstants";

const DEFAULT_TARGET_FORMAT = "epub";
const DEFAULT_IGNORED_FORMATS = ["epub", "pdf"];

/**
 * Conversion settings configuration component.
 *
 * Manages book format conversion preferences:
 * - Auto-convert on import toggle
 * - Target format selection
 * - Ignored formats (comma-separated)
 * - Backup originals toggle
 *
 * Follows SRP by handling only conversion preferences.
 * Follows IOC by using useSetting and useBooleanSetting hooks for persistence.
 */
export function ConversionSettings() {
  const { onBlurChange } = useBlurAfterClick();
  const { getSetting, updateSetting, isLoading } = useSettings();

  // Auto-convert on import
  const { value: autoConvertOnImport, setValue: setAutoConvertOnImport } =
    useBooleanSetting({
      key: AUTO_CONVERT_ON_IMPORT_SETTING_KEY,
      defaultValue: false,
    });

  // Target format
  const { value: targetFormat, setValue: setTargetFormat } = useSetting({
    key: AUTO_CONVERT_TARGET_FORMAT_SETTING_KEY,
    defaultValue: DEFAULT_TARGET_FORMAT,
  });

  // Ignored formats (stored as comma-separated string, managed as Set)
  const [ignoredFormats, setIgnoredFormats] = useState<Set<string>>(
    new Set(DEFAULT_IGNORED_FORMATS),
  );
  const isInitialLoadRef = useRef(true);

  // Load ignored formats on mount
  useEffect(() => {
    if (!isLoading && isInitialLoadRef.current) {
      const savedValue = getSetting(AUTO_CONVERT_IGNORED_FORMATS_SETTING_KEY);
      if (savedValue) {
        try {
          // Try parsing as JSON array first
          const parsed = JSON.parse(savedValue) as string[];
          if (Array.isArray(parsed)) {
            setIgnoredFormats(
              new Set(parsed.map((f) => f.trim().toLowerCase())),
            );
            isInitialLoadRef.current = false;
            return;
          }
        } catch {
          // Not JSON, try comma-separated string
        }
        // Fallback to comma-separated string
        if (savedValue) {
          const formats = savedValue
            .split(",")
            .map((f) => f.trim().toLowerCase())
            .filter((f) => f.length > 0);
          setIgnoredFormats(new Set(formats));
        }
      }
      // Mark initial load as complete after settings are loaded
      setTimeout(() => {
        isInitialLoadRef.current = false;
      }, 0);
    }
  }, [getSetting, isLoading]);

  // Save ignored formats as comma-separated string
  useEffect(() => {
    if (!isInitialLoadRef.current && !isLoading) {
      const formatsArray = Array.from(ignoredFormats).sort();
      const commaSeparated = formatsArray.join(", ");
      updateSetting(AUTO_CONVERT_IGNORED_FORMATS_SETTING_KEY, commaSeparated);
    }
  }, [ignoredFormats, updateSetting, isLoading]);

  // Toggle format in ignored list
  const handleFormatToggle = (format: string) => {
    const formatLower = format.toLowerCase();
    setIgnoredFormats((prev) => {
      const next = new Set(prev);
      if (next.has(formatLower)) {
        next.delete(formatLower);
      } else {
        next.add(formatLower);
      }
      return next;
    });
  };

  // Backup originals
  const { value: backupOriginals, setValue: setBackupOriginals } =
    useBooleanSetting({
      key: AUTO_CONVERT_BACKUP_ORIGINALS_SETTING_KEY,
      defaultValue: false,
    });

  return (
    <div className="flex flex-col gap-6">
      {/* Auto-convert on import */}
      <div className="flex flex-col gap-3">
        <div className="font-medium text-sm text-text-a20">
          Auto-convert on Import
        </div>
        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="checkbox"
            checked={autoConvertOnImport}
            onChange={onBlurChange(() =>
              setAutoConvertOnImport(!autoConvertOnImport),
            )}
            className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
          />
          <span className="text-base text-text-a0">
            Automatically convert books to target format when imported
          </span>
        </label>
      </div>

      {/* Target format */}
      <RadioGroup
        label="Target Format"
        options={[...CONVERSION_TARGET_FORMAT_OPTIONS]}
        value={targetFormat}
        onChange={setTargetFormat}
        name="conversion-target-format"
      />

      {/* Ignored formats */}
      <div className="flex flex-col gap-3">
        <div className="font-medium text-sm text-text-a20">Ignored Formats</div>
        <div className="mb-2 text-sm text-text-a30">
          Select formats to skip during auto-conversion
        </div>
        <div className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8">
          {SUPPORTED_BOOK_FORMATS.map((format) => {
            const isChecked = ignoredFormats.has(format.value);
            return (
              <label
                key={format.value}
                className="flex cursor-pointer items-center gap-2"
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={onBlurChange(() =>
                    handleFormatToggle(format.value),
                  )}
                  className="h-4 w-4 shrink-0 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
                />
                <span className="text-base text-text-a0">{format.label}</span>
              </label>
            );
          })}
        </div>
      </div>

      {/* Backup originals */}
      <div className="flex flex-col gap-3">
        <div className="font-medium text-sm text-text-a20">
          Backup Originals
        </div>
        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="checkbox"
            checked={backupOriginals}
            onChange={onBlurChange(() => setBackupOriginals(!backupOriginals))}
            className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
          />
          <span className="text-base text-text-a0">
            Create backup copies of original files before conversion
          </span>
        </label>
      </div>
    </div>
  );
}
