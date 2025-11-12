import { useEffect } from "react";

export interface UseDropdownClickOutsideOptions {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Reference to the button element (excluded from click outside). */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Reference to the menu element (excluded from click outside). */
  menuRef: React.RefObject<HTMLElement | null>;
  /** Callback when click outside is detected. */
  onClose: () => void;
}

/**
 * Custom hook for detecting clicks outside dropdown menu.
 *
 * Handles click outside detection while excluding both the button
 * and menu elements from triggering the close action.
 * Follows SRP by handling only click outside detection logic.
 * Follows IOC by accepting refs and callback as inputs.
 *
 * Parameters
 * ----------
 * options : UseDropdownClickOutsideOptions
 *     Configuration including open state, refs, and close callback.
 */
export function useDropdownClickOutside({
  isOpen,
  buttonRef,
  menuRef,
  onClose,
}: UseDropdownClickOutsideOptions): void {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;

      // Don't close if clicking on the menu itself
      if (menuRef.current?.contains(target)) {
        return;
      }

      // Don't close if clicking on the button
      if (buttonRef.current?.contains(target)) {
        return;
      }

      // Close if clicking outside both menu and button
      onClose();
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, buttonRef, menuRef, onClose]);
}
