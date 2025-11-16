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

import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";

const SIDEBAR_COLLAPSED_KEY = "sidebar-collapsed";
const DEFAULT_COLLAPSED = false;

/**
 * Safely gets sidebar collapsed state from localStorage.
 *
 * Returns
 * -------
 * boolean | null
 *     Collapsed state from localStorage, or null if not found/invalid.
 */
function getCollapsedFromLocalStorage(): boolean | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
    if (stored === "true" || stored === "false") {
      return stored === "true";
    }
  } catch {
    // localStorage might not be available
  }
  return null;
}

/**
 * Safely saves sidebar collapsed state to localStorage.
 *
 * Parameters
 * ----------
 * collapsed : boolean
 *     Collapsed state to save.
 */
function saveCollapsedToLocalStorage(collapsed: boolean): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed));
  } catch {
    // localStorage might not be available
  }
}

interface SidebarContextType {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

/**
 * Checks if the current viewport is mobile (< 768px).
 *
 * Returns
 * -------
 * boolean
 *     True if viewport width is less than 768px (mobile breakpoint).
 */
function isMobileViewport(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  return window.innerWidth < 768;
}

export function SidebarProvider({ children }: { children: ReactNode }) {
  // Always start with default to avoid hydration mismatch
  // Server and client must render the same initial HTML
  const [isCollapsed, setIsCollapsed] = useState<boolean>(DEFAULT_COLLAPSED);
  const [isHydrated, setIsHydrated] = useState(false);

  // Sync from localStorage after hydration (client-side only)
  // On mobile, default to collapsed (but don't persist to localStorage)
  useEffect(() => {
    const isMobile = isMobileViewport();
    if (isMobile) {
      // Mobile: always start collapsed, don't check localStorage
      setIsCollapsed(true);
    } else {
      // Desktop: check localStorage for saved preference
      const stored = getCollapsedFromLocalStorage();
      if (stored !== null) {
        setIsCollapsed(stored);
      }
    }
    setIsHydrated(true);
  }, []);

  // Persist collapsed state to localStorage when it changes (after hydration)
  // Only persist on desktop, not on mobile (as per requirements)
  useEffect(() => {
    if (isHydrated && !isMobileViewport()) {
      saveCollapsedToLocalStorage(isCollapsed);
    }
  }, [isCollapsed, isHydrated]);

  return (
    <SidebarContext.Provider value={{ isCollapsed, setIsCollapsed }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}
