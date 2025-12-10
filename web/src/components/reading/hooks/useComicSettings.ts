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

import { useCallback } from "react";
import {
  COMIC_READING_DIRECTION_SETTING_KEY,
  COMIC_READING_MODE_SETTING_KEY,
  COMIC_SPREAD_MODE_SETTING_KEY,
  COMIC_ZOOM_LEVEL_SETTING_KEY,
} from "@/components/profile/config/configurationConstants";
import { useSetting } from "@/hooks/useSetting";
import type { ComicReadingDirection, ComicReadingMode } from "../ComicReader";

const DEFAULT_READING_MODE: ComicReadingMode = "paged";
const DEFAULT_READING_DIRECTION: ComicReadingDirection = "ltr";
const DEFAULT_SPREAD_MODE = true;
const DEFAULT_ZOOM_LEVEL = 1.0;

export interface UseComicSettingsOptions {
  /**
   * Optional book ID.
   * Currently unused as settings are global, but kept for interface compatibility.
   */
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
 * Persists settings to user profile via useSetting hook.
 * Follows SRP by focusing solely on settings management.
 *
 * Parameters
 * ----------
 * options : UseComicSettingsOptions
 *     Options including optional book ID (currently unused).
 *
 * Returns
 * -------
 * UseComicSettingsResult
 *     Settings state and update methods.
 */
export function useComicSettings({
  bookId: _bookId,
}: UseComicSettingsOptions = {}): UseComicSettingsResult {
  const { value: readingModeStr, setValue: setReadingModeStr } = useSetting({
    key: COMIC_READING_MODE_SETTING_KEY,
    defaultValue: DEFAULT_READING_MODE,
  });

  const { value: readingDirectionStr, setValue: setReadingDirectionStr } =
    useSetting({
      key: COMIC_READING_DIRECTION_SETTING_KEY,
      defaultValue: DEFAULT_READING_DIRECTION,
    });

  const { value: spreadModeStr, setValue: setSpreadModeStr } = useSetting({
    key: COMIC_SPREAD_MODE_SETTING_KEY,
    defaultValue: String(DEFAULT_SPREAD_MODE),
  });

  const { value: zoomLevelStr, setValue: setZoomLevelStr } = useSetting({
    key: COMIC_ZOOM_LEVEL_SETTING_KEY,
    defaultValue: String(DEFAULT_ZOOM_LEVEL),
  });

  // Parse values
  const readingMode =
    (readingModeStr as ComicReadingMode) || DEFAULT_READING_MODE;
  const readingDirection =
    (readingDirectionStr as ComicReadingDirection) || DEFAULT_READING_DIRECTION;
  const spreadMode = String(spreadModeStr) === "true";
  const zoomLevel = parseFloat(String(zoomLevelStr)) || DEFAULT_ZOOM_LEVEL;

  const setReadingMode = useCallback(
    (mode: ComicReadingMode) => {
      setReadingModeStr(mode);
    },
    [setReadingModeStr],
  );

  const setReadingDirection = useCallback(
    (direction: ComicReadingDirection) => {
      setReadingDirectionStr(direction);
    },
    [setReadingDirectionStr],
  );

  const setSpreadMode = useCallback(
    (enabled: boolean) => {
      setSpreadModeStr(String(enabled));
    },
    [setSpreadModeStr],
  );

  const setZoomLevel = useCallback(
    (level: number) => {
      const validLevel = Math.max(0.5, Math.min(3.0, level));
      setZoomLevelStr(String(validLevel));
    },
    [setZoomLevelStr],
  );

  const resetSettings = useCallback(() => {
    setReadingModeStr(DEFAULT_READING_MODE);
    setReadingDirectionStr(DEFAULT_READING_DIRECTION);
    setSpreadModeStr(String(DEFAULT_SPREAD_MODE));
    setZoomLevelStr(String(DEFAULT_ZOOM_LEVEL));
  }, [
    setReadingModeStr,
    setReadingDirectionStr,
    setSpreadModeStr,
    setZoomLevelStr,
  ]);

  return {
    readingMode,
    setReadingMode,
    readingDirection,
    setReadingDirection,
    spreadMode,
    setSpreadMode,
    zoomLevel,
    setZoomLevel,
    resetSettings,
  };
}
