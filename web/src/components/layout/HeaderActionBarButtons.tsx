"use client";

import { useUser } from "@/contexts/UserContext";
import { AdminButton } from "./AdminButton";
import { useRegisterHeaderButton } from "./hooks/useRegisterHeaderButton";
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
 * Follows SOC by delegating registration lifecycle to useRegisterHeaderButton hook.
 */
export function HeaderActionBarButtons() {
  const { user } = useUser();

  // Register profile button (ProfileButton uses useUser internally and will update automatically)
  useRegisterHeaderButton("profile", <ProfileButton />);

  // Conditionally register admin button based on user permissions
  // Always call hook, but pass null element when user is not admin
  useRegisterHeaderButton("admin", user?.is_admin ? <AdminButton /> : null);

  return null;
}
