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

import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useState } from "react";

/**
 * Represents a button in the header action bar.
 */
export interface HeaderActionButton {
  /**
   * Unique identifier for the button.
   */
  id: string;
  /**
   * React node to render as the button.
   */
  element: ReactNode;
}

interface HeaderActionBarContextType {
  /**
   * Register a button to be displayed in the header action bar.
   *
   * Parameters
   * ----------
   * button : HeaderActionButton
   *     Button to register.
   */
  registerButton: (button: HeaderActionButton) => void;
  /**
   * Unregister a button from the header action bar.
   *
   * Parameters
   * ----------
   * id : string
   *     ID of the button to unregister.
   */
  unregisterButton: (id: string) => void;
  /**
   * Array of all registered buttons.
   */
  buttons: HeaderActionButton[];
}

const HeaderActionBarContext = createContext<
  HeaderActionBarContextType | undefined
>(undefined);

interface HeaderActionBarProviderProps {
  children: ReactNode;
}

/**
 * Provider component for header action bar context.
 *
 * Manages the state of buttons registered for the header action bar.
 * Follows IOC by providing a context-based dependency injection system.
 *
 * Parameters
 * ----------
 * props : HeaderActionBarProviderProps
 *     Component props including children.
 */
export function HeaderActionBarProvider({
  children,
}: HeaderActionBarProviderProps) {
  const [buttons, setButtons] = useState<HeaderActionButton[]>([]);

  const registerButton = useCallback((button: HeaderActionButton) => {
    setButtons((prev) => {
      const existingIndex = prev.findIndex((b) => b.id === button.id);
      if (existingIndex >= 0) {
        // Replace in place to maintain order
        const updated = [...prev];
        updated[existingIndex] = button;
        return updated;
      }
      // Append new button to maintain registration order
      return [...prev, button];
    });
  }, []);

  const unregisterButton = useCallback((id: string) => {
    setButtons((prev) => prev.filter((b) => b.id !== id));
  }, []);

  return (
    <HeaderActionBarContext.Provider
      value={{ registerButton, unregisterButton, buttons }}
    >
      {children}
    </HeaderActionBarContext.Provider>
  );
}

/**
 * Hook to access header action bar context.
 *
 * Returns
 * -------
 * HeaderActionBarContextType
 *     Context value with methods to register/unregister buttons.
 *
 * Raises
 * ------
 * Error
 *     If used outside of HeaderActionBarProvider.
 */
export function useHeaderActionBar() {
  const context = useContext(HeaderActionBarContext);
  if (context === undefined) {
    throw new Error(
      "useHeaderActionBar must be used within a HeaderActionBarProvider",
    );
  }
  return context;
}
