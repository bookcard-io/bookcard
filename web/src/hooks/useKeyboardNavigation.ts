import { useEffect } from "react";

export interface KeyboardNavigationOptions {
  /** Callback when Escape key is pressed. */
  onEscape?: () => void;
  /** Callback when ArrowLeft key is pressed. */
  onArrowLeft?: () => void;
  /** Callback when ArrowRight key is pressed. */
  onArrowRight?: () => void;
  /** Whether keyboard navigation is enabled. */
  enabled?: boolean;
}

/**
 * Custom hook for keyboard navigation.
 *
 * Handles keyboard events for navigation (Escape, ArrowLeft, ArrowRight).
 * Follows SRP by focusing solely on keyboard event handling.
 * Uses IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : KeyboardNavigationOptions
 *     Navigation options with callbacks.
 */
export function useKeyboardNavigation(
  options: KeyboardNavigationOptions,
): void {
  const { onEscape, onArrowLeft, onArrowRight, enabled = true } = options;

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && onEscape) {
        e.preventDefault();
        onEscape();
      } else if (e.key === "ArrowLeft" && onArrowLeft) {
        e.preventDefault();
        onArrowLeft();
      } else if (e.key === "ArrowRight" && onArrowRight) {
        e.preventDefault();
        onArrowRight();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [enabled, onEscape, onArrowLeft, onArrowRight]);
}
