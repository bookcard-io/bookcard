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

import { useCallback, useEffect, useState } from "react";
import {
  exitFullscreen,
  getFullscreenChangeEventName,
  isFullscreen,
  requestFullscreen,
} from "@/utils/fullscreenApi";

export interface UseFullscreenResult {
  /** Whether the document is currently in fullscreen mode. */
  isFullscreen: boolean;
  /** Toggle fullscreen mode. */
  toggleFullscreen: () => void;
}

/**
 * Custom hook for managing fullscreen state.
 *
 * Handles fullscreen API interactions and state synchronization.
 * Follows SRP by isolating fullscreen management logic.
 * Follows IOC by returning state and actions.
 * Follows DRY by using shared fullscreen API utilities.
 *
 * Returns
 * -------
 * UseFullscreenResult
 *     Fullscreen state and toggle function.
 */
export function useFullscreen(): UseFullscreenResult {
  const [isFullscreenState, setIsFullscreenState] = useState(false);

  // Initialize state from current fullscreen status
  useEffect(() => {
    setIsFullscreenState(isFullscreen());
  }, []);

  const toggleFullscreen = useCallback(async () => {
    try {
      if (isFullscreenState) {
        await exitFullscreen();
      } else {
        await requestFullscreen();
      }
      // State will be updated by the event listener, not here
      // This prevents race conditions and ensures accurate state
    } catch (error) {
      // Handle errors silently or log if needed
      // Fullscreen may fail due to user gesture requirements or browser policies
      console.warn("Failed to toggle fullscreen:", error);
    }
  }, [isFullscreenState]);

  // Sync state with browser fullscreen events
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreenState(isFullscreen());
    };

    const eventName = getFullscreenChangeEventName();
    document.addEventListener(eventName, handleFullscreenChange);
    return () => {
      document.removeEventListener(eventName, handleFullscreenChange);
    };
  }, []);

  return {
    isFullscreen: isFullscreenState,
    toggleFullscreen,
  };
}
