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

import { useContext, useEffect, useState } from "react";
import { UserContext } from "@/contexts/UserContext";

const THEME_SETTING_KEY = "theme";
const THEME_LOCALSTORAGE_KEY = "theme-preference";
const DEFAULT_THEME = "dark";

/**
 * Safely gets theme from localStorage.
 *
 * Returns
 * -------
 * "dark" | "light" | null
 *     Theme value from localStorage, or null if not found/invalid.
 */
function getThemeFromLocalStorage(): "dark" | "light" | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const stored = localStorage.getItem(THEME_LOCALSTORAGE_KEY);
    if (stored === "dark" || stored === "light") {
      return stored;
    }
  } catch {
    // localStorage might not be available
  }
  return null;
}

/**
 * Safely saves theme to localStorage.
 *
 * Parameters
 * ----------
 * theme : "dark" | "light"
 *     Theme value to save.
 */
function saveThemeToLocalStorage(theme: "dark" | "light"): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    localStorage.setItem(THEME_LOCALSTORAGE_KEY, theme);
  } catch {
    // localStorage might not be available
  }
}

/**
 * Custom hook for managing application theme.
 *
 * Handles theme state persistence and applies theme to HTML element.
 * Works with or without UserProvider by using localStorage as fallback.
 * Syncs with backend when UserProvider becomes available.
 * Follows SRP by handling only theme management.
 *
 * Returns
 * -------
 * object
 *     Theme value, toggle function, and loading state.
 */
export function useTheme() {
  // Initialize theme from localStorage immediately (before UserProvider is available)
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof window !== "undefined") {
      const stored = getThemeFromLocalStorage();
      if (stored) {
        return stored;
      }
    }
    return DEFAULT_THEME;
  });

  // Get UserContext, but it may be undefined if UserProvider is not available
  const userContext = useContext(UserContext);

  // Load theme from backend settings when UserProvider becomes available
  useEffect(() => {
    if (userContext && !userContext.isLoading) {
      const savedTheme = userContext.getSetting(THEME_SETTING_KEY);
      if (savedTheme === "dark" || savedTheme === "light") {
        setTheme(savedTheme);
        saveThemeToLocalStorage(savedTheme);
      } else {
        // Backend doesn't have theme, sync localStorage to backend
        const localTheme = getThemeFromLocalStorage();
        if (localTheme) {
          userContext.updateSetting(THEME_SETTING_KEY, localTheme);
        }
      }
    }
  }, [userContext?.isLoading, userContext?.getSetting, userContext]);

  // Apply theme to HTML element immediately
  useEffect(() => {
    if (typeof document !== "undefined") {
      const html = document.documentElement;
      html.setAttribute("data-theme", theme);
    }
  }, [theme]);

  /**
   * Toggles between dark and light theme.
   */
  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    saveThemeToLocalStorage(newTheme);
    // Sync with backend if available
    if (userContext) {
      userContext.updateSetting(THEME_SETTING_KEY, newTheme);
    }
  };

  return {
    theme,
    toggleTheme,
    isLoading: userContext?.isLoading ?? false,
  };
}
