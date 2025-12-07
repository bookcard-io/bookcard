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

import { useCallback, useEffect, useState } from "react";
import type { ComicReadingDirection, ComicReadingMode } from "../ComicReader";

const STORAGE_KEY_PREFIX = "comic_reader_settings_";

interface ComicSettings {
  readingMode: ComicReadingMode;
  readingDirection: ComicReadingDirection;
  spreadMode: boolean;
  zoomLevel: number;
}

const DEFAULT_SETTINGS: ComicSettings = {
  readingMode: "paged",
  readingDirection: "ltr",
  spreadMode: true,
  zoomLevel: 1.0,
};

export interface UseComicSettingsOptions {
  bookId?: number;
}

export interface UseComicSettingsResult {
  readingMode: ComicReadingMode;
  setReadingMode: (mode: ComicReadingMode) => void;
  readingDirection: ComicReadingDirection;
  setReadingDirection: (direction: ComicReadingDirection) => void;
  spreadMode: boolean;
  setSpreadMode: (enabled: boolean) => void;
  zoomLevel: number;
  setZoomLevel: (level: number) => void;
  resetSettings: () => void;
}

/**
 * Hook for managing comic reading settings.
 *
 * Stores settings in localStorage with optional book-specific storage.
 * Follows SRP by focusing solely on settings management.
 *
 * Parameters
 * ----------
 * options : UseComicSettingsOptions
 *     Options including optional book ID for book-specific settings.
 *
 * Returns
 * -------
 * UseComicSettingsResult
 *     Settings state and update methods.
 */
export function useComicSettings({
  bookId,
}: UseComicSettingsOptions = {}): UseComicSettingsResult {
  const storageKey = bookId
    ? `${STORAGE_KEY_PREFIX}book_${bookId}`
    : `${STORAGE_KEY_PREFIX}global`;

  const [settings, setSettings] = useState<ComicSettings>(() => {
    if (typeof window === "undefined") {
      return DEFAULT_SETTINGS;
    }

    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
      }
    } catch {
      // Ignore parse errors
    }

    return DEFAULT_SETTINGS;
  });

  // Reload settings when storage key changes (e.g., bookId updates)
  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(stored) });
      } else {
        setSettings(DEFAULT_SETTINGS);
      }
    } catch {
      setSettings(DEFAULT_SETTINGS);
    }
  }, [storageKey]);

  // Save to localStorage whenever settings change
  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      localStorage.setItem(storageKey, JSON.stringify(settings));
    } catch {
      // Ignore storage errors
    }
  }, [settings, storageKey]);

  const setReadingMode = useCallback((mode: ComicReadingMode) => {
    setSettings((prev) => ({ ...prev, readingMode: mode }));
  }, []);

  const setReadingDirection = useCallback(
    (direction: ComicReadingDirection) => {
      setSettings((prev) => ({ ...prev, readingDirection: direction }));
    },
    [],
  );

  const setSpreadMode = useCallback((enabled: boolean) => {
    setSettings((prev) => ({ ...prev, spreadMode: enabled }));
  }, []);

  const setZoomLevel = useCallback((level: number) => {
    setSettings((prev) => ({
      ...prev,
      zoomLevel: Math.max(0.5, Math.min(3.0, level)),
    }));
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
  }, []);

  return {
    readingMode: settings.readingMode,
    setReadingMode,
    readingDirection: settings.readingDirection,
    setReadingDirection,
    spreadMode: settings.spreadMode,
    setSpreadMode,
    zoomLevel: settings.zoomLevel,
    setZoomLevel,
    resetSettings,
  };
}
