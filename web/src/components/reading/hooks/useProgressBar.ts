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

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Hook for managing progress bar state and tooltip visibility.
 *
 * Follows SRP by focusing solely on progress bar state management.
 * Follows IOC by providing state management logic that can be injected.
 *
 * Parameters
 * ----------
 * progress : number
 *     Current progress value (0.0 to 1.0).
 * isDisabled : boolean
 *     Whether the progress bar is disabled.
 *
 * Returns
 * -------
 * object
 *     Object containing:
 *     - localProgress: Current local progress value
 *     - showTooltip: Whether to show the loading tooltip
 *     - handleProgressChange: Handler for progress input changes
 */
export function useProgressBar(progress: number, isDisabled: boolean) {
  const [localProgress, setLocalProgress] = useState(progress);
  const [showTooltip, setShowTooltip] = useState(false);
  const tooltipTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Sync localProgress with progress prop when it changes
  // This ensures the progress bar reflects navigation to persisted location
  useEffect(() => {
    setLocalProgress(progress);
  }, [progress]);

  // Show tooltip when disabled, auto-dismiss when enabled
  useEffect(() => {
    if (isDisabled) {
      setShowTooltip(true);
      // Clear any existing timeout
      if (tooltipTimeoutRef.current) {
        clearTimeout(tooltipTimeoutRef.current);
      }
    } else {
      // Auto-dismiss tooltip after a short delay when enabled
      tooltipTimeoutRef.current = setTimeout(() => {
        setShowTooltip(false);
      }, 2000);
    }

    return () => {
      if (tooltipTimeoutRef.current) {
        clearTimeout(tooltipTimeoutRef.current);
      }
    };
  }, [isDisabled]);

  const handleProgressChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newProgress = parseFloat(e.target.value);
      setLocalProgress(newProgress);
      return newProgress;
    },
    [],
  );

  return {
    localProgress,
    showTooltip,
    handleProgressChange,
  };
}
