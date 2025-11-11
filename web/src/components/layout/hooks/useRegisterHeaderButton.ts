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
