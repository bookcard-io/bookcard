import { useEffect } from "react";

/**
 * Custom hook for modal behavior.
 *
 * Manages body scroll lock when modal is open.
 * Follows SRP by focusing solely on modal lifecycle management.
 *
 * Parameters
 * ----------
 * isOpen : boolean
 *     Whether the modal is open.
 */
export function useModal(isOpen: boolean): void {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = "auto";
      };
    }
    return undefined;
  }, [isOpen]);
}
