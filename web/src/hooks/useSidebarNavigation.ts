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

  const scrollToManageDevices = useCallback(() => {
    if (typeof document === "undefined") {
      return false;
    }
    const element = document.getElementById("manage-devices");
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      return true;
    }
    return false;
  }, []);

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
    // If already on profile, just scroll.
    if (pathname === "/profile") {
      scrollToManageDevices();
      return;
    }

    // Navigate to profile page and keep trying to scroll until the element exists
    router.push("/profile#manage-devices");

    let attempts = 0;
    const maxAttempts = 20;
    const intervalMs = 100;

    const intervalId = window.setInterval(() => {
      attempts += 1;
      const didScroll = scrollToManageDevices();
      if (didScroll || attempts >= maxAttempts) {
        window.clearInterval(intervalId);
      }
    }, intervalMs);
  }, [router, pathname, scrollToManageDevices]);

  const isAdminActive = pathname === "/admin";

  return {
    navigateHome,
    navigateToShelves,
    navigateToAdmin,
    navigateToManageDevices,
    isAdminActive,
  };
}
