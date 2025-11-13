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

import { createContext, type ReactNode, useContext, useState } from "react";

interface SelectedShelfContextType {
  /** Currently selected shelf ID (undefined means no shelf selected). */
  selectedShelfId: number | undefined;
  /** Set the selected shelf ID. */
  setSelectedShelfId: (shelfId: number | undefined) => void;
}

const SelectedShelfContext = createContext<
  SelectedShelfContextType | undefined
>(undefined);

/**
 * Provider for selected shelf context.
 *
 * Manages the currently selected shelf for filtering books.
 * Follows SRP by managing only shelf selection state.
 */
export function SelectedShelfProvider({ children }: { children: ReactNode }) {
  const [selectedShelfId, setSelectedShelfId] = useState<number | undefined>(
    undefined,
  );

  return (
    <SelectedShelfContext.Provider
      value={{ selectedShelfId, setSelectedShelfId }}
    >
      {children}
    </SelectedShelfContext.Provider>
  );
}

/**
 * Hook to access selected shelf context.
 *
 * Returns
 * -------
 * SelectedShelfContextType
 *     Selected shelf ID and setter function.
 *
 * Raises
 * ------
 * Error
 *     If used outside of SelectedShelfProvider.
 */
export function useSelectedShelf() {
  const context = useContext(SelectedShelfContext);
  if (context === undefined) {
    throw new Error(
      "useSelectedShelf must be used within a SelectedShelfProvider",
    );
  }
  return context;
}
