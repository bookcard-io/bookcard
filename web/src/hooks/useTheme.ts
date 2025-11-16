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
import { THEME_PREFERENCE_SETTING_KEY } from "@/components/profile/config/configurationConstants";
import { UserContext } from "@/contexts/UserContext";

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
  // Always start with default to avoid hydration mismatch
  // Server and client must render the same initial HTML
  const [theme, setTheme] = useState<"dark" | "light">(DEFAULT_THEME);
  const [isHydrated, setIsHydrated] = useState(false);

  // Get UserContext, but it may be undefined if UserProvider is not available
  const userContext = useContext(UserContext);

  // Sync from localStorage after hydration (client-side only)
  useEffect(() => {
    const stored = getThemeFromLocalStorage();
    if (stored) {
      setTheme(stored);
    }
    setIsHydrated(true);
  }, []);

  // Load theme from backend settings when UserProvider becomes available
  // Also watch for setting changes to sync theme when updated from other components
  // Only run after hydration to avoid conflicts
  useEffect(() => {
    if (isHydrated && userContext && !userContext.isLoading) {
      const savedTheme = userContext.getSetting(THEME_PREFERENCE_SETTING_KEY);
      if (savedTheme === "dark" || savedTheme === "light") {
        // Only update if different to avoid unnecessary re-renders
        if (savedTheme !== theme) {
          setTheme(savedTheme);
          saveThemeToLocalStorage(savedTheme);
        }
      } else {
        // Backend doesn't have theme, sync localStorage to backend
        const localTheme = getThemeFromLocalStorage();
        if (localTheme) {
          userContext.updateSetting(THEME_PREFERENCE_SETTING_KEY, localTheme);
        }
      }
    }
  }, [
    isHydrated,
    userContext?.isLoading,
    userContext?.getSetting,
    userContext,
    userContext?.settings,
    theme,
  ]);

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
      userContext.updateSetting(THEME_PREFERENCE_SETTING_KEY, newTheme);
    }
  };

  return {
    theme,
    toggleTheme,
    isLoading: userContext?.isLoading ?? false,
  };
}
