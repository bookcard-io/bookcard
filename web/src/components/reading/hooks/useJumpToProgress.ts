// Copyright (C) 2025 khoa and others
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

import { useEffect } from "react";
import type { JumpToProgressHandlerOptions } from "@/utils/epubLocationHandlers";
import { createJumpToProgressHandler } from "@/utils/epubLocationHandlers";

/**
 * Hook to register jump to progress handler with parent component.
 *
 * Creates a handler function that jumps to a specific progress position
 * in the EPUB and registers it with the parent via callback.
 *
 * Parameters
 * ----------
 * options : JumpToProgressHandlerOptions
 *     Options for creating the jump handler.
 * onJumpToProgress : ((handler: ((progress: number) => void) | null) => void) | undefined
 *     Callback to register the jump handler with parent.
 */
export function useJumpToProgress(
  options: JumpToProgressHandlerOptions,
  onJumpToProgress?: (handler: ((progress: number) => void) | null) => void,
) {
  const {
    bookRef,
    renditionRef,
    isNavigatingRef,
    setLocation,
    onLocationChange,
  } = options;

  useEffect(() => {
    if (!onJumpToProgress) {
      return;
    }

    const jumpToProgress = createJumpToProgressHandler({
      bookRef,
      renditionRef,
      isNavigatingRef,
      setLocation,
      onLocationChange,
    });

    onJumpToProgress(jumpToProgress);

    return () => {
      onJumpToProgress(null);
    };
    // Refs are stable objects and don't need to be in deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    onJumpToProgress,
    setLocation,
    onLocationChange,
    bookRef,
    isNavigatingRef,
    renditionRef,
  ]);
}
