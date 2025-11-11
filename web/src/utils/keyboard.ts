/**
 * Utility functions for keyboard event handling.
 *
 * Provides reusable keyboard event handlers following DRY principle.
 */

/**
 * Creates a keyboard handler that triggers on Enter or Space.
 *
 * Parameters
 * ----------
 * handler : () => void
 *     Callback to execute when Enter or Space is pressed.
 *
 * Returns
 * -------
 * (e: React.KeyboardEvent) => void
 *     Keyboard event handler function.
 */
export function createEnterSpaceHandler(
  handler: () => void,
): (e: React.KeyboardEvent) => void {
  return (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handler();
    }
  };
}
