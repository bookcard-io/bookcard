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

import { createContext, type ReactNode, useCallback, useContext } from "react";

interface BlurAfterClickContextType {
  /**
   * Creates an onChange handler that blurs the element after the change.
   * For checkboxes and radio buttons that need to blur after interaction.
   */
  onBlurChange: (
    handler: (e: React.ChangeEvent<HTMLInputElement>) => void,
  ) => (e: React.ChangeEvent<HTMLInputElement>) => void;
  /**
   * Creates an onClick handler that blurs the element after the click.
   * For buttons and other clickable elements that need to blur after interaction.
   */
  onBlurClick: (
    handler: (e: React.MouseEvent<HTMLElement>) => void,
  ) => (e: React.MouseEvent<HTMLElement>) => void;
}

const BlurAfterClickContext = createContext<
  BlurAfterClickContextType | undefined
>(undefined);

interface BlurAfterClickProviderProps {
  /**
   * Child components that can access the blur after click context.
   */
  children: ReactNode;
}

/**
 * Provider component for blur after click context.
 *
 * Provides handlers that automatically blur elements after interaction.
 * Follows SRP by handling only blur behavior management.
 * Follows IOC by providing context-based dependency injection.
 *
 * Parameters
 * ----------
 * props : BlurAfterClickProviderProps
 *     Component props including children.
 */
export function BlurAfterClickProvider({
  children,
}: BlurAfterClickProviderProps) {
  const onBlurChange = useCallback(
    (handler: (e: React.ChangeEvent<HTMLInputElement>) => void) => {
      return (e: React.ChangeEvent<HTMLInputElement>) => {
        handler(e);
        e.currentTarget.blur();
      };
    },
    [],
  );

  const onBlurClick = useCallback(
    (handler: (e: React.MouseEvent<HTMLElement>) => void) => {
      return (e: React.MouseEvent<HTMLElement>) => {
        handler(e);
        e.currentTarget.blur();
      };
    },
    [],
  );

  return (
    <BlurAfterClickContext.Provider value={{ onBlurChange, onBlurClick }}>
      {children}
    </BlurAfterClickContext.Provider>
  );
}

/**
 * Hook to access blur after click context.
 *
 * Returns
 * -------
 * BlurAfterClickContextType
 *     Context value with methods to create blur-enabled event handlers.
 *
 * Raises
 * ------
 * Error
 *     If used outside of BlurAfterClickProvider.
 */
export function useBlurAfterClick(): BlurAfterClickContextType {
  const context = useContext(BlurAfterClickContext);
  if (context === undefined) {
    throw new Error(
      "useBlurAfterClick must be used within a BlurAfterClickProvider",
    );
  }
  return context;
}
