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

import { useEffect, useState } from "react";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";

export interface UseThemeSettingsPanelOptions {
  /** Whether the panel is open. */
  isOpen: boolean;
  /** Callback when the panel should be closed. */
  onClose: () => void;
}

export interface UseThemeSettingsPanelResult {
  /** Whether the overlay should be visible. */
  showOverlay: boolean;
  /** Function to hide the overlay. */
  hideOverlay: () => void;
}

/**
 * Custom hook for managing theme settings panel state.
 *
 * Handles overlay visibility and keyboard navigation.
 * Follows SRP by managing only panel-related state.
 * Follows SOC by separating state management from UI.
 * Follows IOC by accepting configuration options.
 *
 * Parameters
 * ----------
 * options : UseThemeSettingsPanelOptions
 *     Hook options including open state and close handler.
 *
 * Returns
 * -------
 * UseThemeSettingsPanelResult
 *     Overlay visibility state and control function.
 */
export function useThemeSettingsPanel({
  isOpen,
  onClose,
}: UseThemeSettingsPanelOptions): UseThemeSettingsPanelResult {
  const [showOverlay, setShowOverlay] = useState(true);

  // Reset overlay visibility when panel opens
  useEffect(() => {
    if (isOpen) {
      setShowOverlay(true);
    }
  }, [isOpen]);

  // Handle keyboard navigation
  useKeyboardNavigation({
    onEscape: onClose,
    enabled: isOpen,
  });

  const hideOverlay = () => {
    setShowOverlay(false);
  };

  return {
    showOverlay,
    hideOverlay,
  };
}
