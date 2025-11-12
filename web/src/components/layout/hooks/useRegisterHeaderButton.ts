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

import type { ReactNode } from "react";
import { useEffect } from "react";
import { useHeaderActionBar } from "@/contexts/HeaderActionBarContext";

/**
 * Hook to register a button in the header action bar.
 *
 * Automatically registers the button on mount and unregisters on unmount.
 * If element is null, the button is unregistered.
 * Follows SRP by only handling button registration lifecycle.
 * Follows IOC by using context for dependency injection.
 *
 * Parameters
 * ----------
 * buttonId : string
 *     Unique identifier for the button.
 * element : ReactNode | null
 *     React node to render as the button, or null to unregister.
 *
 * Examples
 * --------
 * ```tsx
 * useRegisterHeaderButton("profile", <ProfileButton />);
 * useRegisterHeaderButton("admin", isAdmin ? <AdminButton /> : null);
 * ```
 */
export function useRegisterHeaderButton(
  buttonId: string,
  element: ReactNode | null,
): void {
  const { registerButton, unregisterButton } = useHeaderActionBar();

  useEffect(() => {
    if (element !== null) {
      registerButton({ id: buttonId, element });
    } else {
      unregisterButton(buttonId);
    }
    return () => {
      unregisterButton(buttonId);
    };
  }, [buttonId, element, registerButton, unregisterButton]);
}
