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

import { usePathname, useRouter } from "next/navigation";
import { useCallback } from "react";
import { useSelectedShelf } from "@/contexts/SelectedShelfContext";

export interface UseSidebarNavigationResult {
  /** Navigate to home page. */
  navigateHome: () => void;
  /** Navigate to shelves management. */
  navigateToShelves: () => void;
  /** Navigate to admin page. */
  navigateToAdmin: () => void;
  /** Navigate to profile and scroll to manage-devices section. */
  navigateToManageDevices: () => void;
  /** Check if admin page is active. */
  isAdminActive: boolean;
}

/**
 * Hook for managing sidebar navigation.
 *
 * Provides navigation handlers for sidebar actions.
 * Follows SRP by handling only navigation logic.
 * Follows IOC by using Next.js router.
 *
 * Returns
 * -------
 * UseSidebarNavigationResult
 *     Object containing navigation functions and state.
 */
export function useSidebarNavigation(): UseSidebarNavigationResult {
  const router = useRouter();
  const pathname = usePathname();
  const { setSelectedShelfId } = useSelectedShelf();

  const navigateHome = useCallback(() => {
    setSelectedShelfId(undefined);
    router.push("/");
  }, [router, setSelectedShelfId]);

  const navigateToShelves = useCallback(() => {
    router.push("/?tab=shelves");
  }, [router]);

  const navigateToAdmin = useCallback(() => {
    router.push("/admin");
  }, [router]);

  const navigateToManageDevices = useCallback(() => {
    // Navigate to profile page and scroll to manage-devices section
    if (pathname === "/profile") {
      // Already on profile page, scroll immediately
      const element = document.getElementById("manage-devices");
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } else {
      // Navigate to profile page first, then scroll after navigation
      router.push("/profile");
      setTimeout(() => {
        const element = document.getElementById("manage-devices");
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    }
  }, [router, pathname]);

  const isAdminActive = pathname === "/admin";

  return {
    navigateHome,
    navigateToShelves,
    navigateToAdmin,
    navigateToManageDevices,
    isAdminActive,
  };
}
