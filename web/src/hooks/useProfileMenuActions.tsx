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

import { useRouter } from "next/navigation";
import { useCallback, useMemo } from "react";
import { FaCog } from "react-icons/fa";
import type { DropdownMenuItemProps } from "@/components/common/DropdownMenuItem";
import { getToggleThemeLabel } from "@/components/profile/config/configurationConstants";
import { useTheme } from "@/hooks/useTheme";

export interface UseProfileMenuActionsOptions {
  /** Callback when menu should be closed. */
  onClose: () => void;
}

export interface UseProfileMenuActionsResult {
  /** Handler for profile header and "View profile" navigation. */
  onViewProfile: () => void;
  /** Menu items to render in the profile dropdown. */
  items: DropdownMenuItemProps[];
}

/**
 * Custom hook for profile menu actions.
 *
 * Provides handlers and menu item definitions for the profile dropdown.
 * Follows SRP by managing only menu action handlers and their presentation data.
 * Follows SOC by keeping ProfileMenu as a render-only wrapper.
 *
 * Parameters
 * ----------
 * options : UseProfileMenuActionsOptions
 *     Configuration including close callback.
 *
 * Returns
 * -------
 * UseProfileMenuActionsResult
 *     Action handlers and menu item definitions.
 */
export function useProfileMenuActions({
  onClose,
}: UseProfileMenuActionsOptions): UseProfileMenuActionsResult {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();

  const onViewProfile = useCallback(() => {
    router.push("/profile");
    onClose();
  }, [onClose, router]);

  const onViewConfigurations = useCallback(() => {
    router.push("/profile/configurations");
    onClose();
  }, [onClose, router]);

  const onToggleTheme = useCallback(() => {
    toggleTheme();
    onClose();
  }, [onClose, toggleTheme]);

  const onLogout = useCallback(async () => {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } finally {
      // Even if logout fails, redirect to login.
      router.push("/login");
      router.refresh();
      onClose();
    }
  }, [onClose, router]);

  const items: DropdownMenuItemProps[] = useMemo(
    () => [
      {
        icon: "pi pi-id-card",
        label: "View profile",
        onClick: onViewProfile,
        className: "cursor-pointer",
      },
      {
        icon: <FaCog className="text-base" aria-hidden="true" />,
        label: "Configurations",
        onClick: onViewConfigurations,
        className: "cursor-pointer",
      },
      {
        icon: theme === "dark" ? "pi pi-sun" : "pi pi-moon",
        label: getToggleThemeLabel(theme),
        onClick: onToggleTheme,
        className: "cursor-pointer",
      },
      {
        icon: "pi pi-sign-out",
        label: "Logout",
        onClick: () => {
          void onLogout();
        },
        className: "cursor-pointer",
      },
    ],
    [onLogout, onToggleTheme, onViewConfigurations, onViewProfile, theme],
  );

  return {
    onViewProfile,
    items,
  };
}
