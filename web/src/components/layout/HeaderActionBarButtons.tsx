"use client";

import { useEffect } from "react";
import { useHeaderActionBar } from "@/contexts/HeaderActionBarContext";
import { useUser } from "@/contexts/UserContext";
import { AdminButton } from "./AdminButton";
import { ProfileButton } from "./ProfileButton";

/**
 * Component that registers standard header action bar buttons.
 *
 * Automatically registers ProfileButton and conditionally registers AdminButton
 * based on user permissions. This is the single place to manage which buttons
 * appear in the header action bar.
 *
 * Follows DRY by centralizing button registration logic.
 * Follows SRP by only handling button registration.
 * Follows IOC by using context for user data.
 */
export function HeaderActionBarButtons() {
  const { user } = useUser();
  const { registerButton, unregisterButton } = useHeaderActionBar();

  // Register profile button (ProfileButton uses useUser internally and will update automatically)
  useEffect(() => {
    registerButton({ id: "profile", element: <ProfileButton /> });
    return () => {
      unregisterButton("profile");
    };
  }, [registerButton, unregisterButton]);

  // Register/unregister admin button based on user permissions
  useEffect(() => {
    if (user?.is_admin) {
      registerButton({ id: "admin", element: <AdminButton /> });
    }
    // Cleanup function handles unregistering when user is not admin or component unmounts
    return () => {
      unregisterButton("admin");
    };
  }, [user?.is_admin, registerButton, unregisterButton]);

  return null;
}
