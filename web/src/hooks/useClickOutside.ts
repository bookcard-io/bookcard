import { useEffect, useRef } from "react";

/**
 * Custom hook for detecting clicks outside a component.
 *
 * Parameters
 * ----------
 * handler : () => void
 *     Callback function to execute when click outside is detected.
 * enabled : boolean
 *     Whether the click outside detection is enabled (default: true).
 *
 * Returns
 * -------
 * React.RefObject<T>
 *     Ref object to attach to the element to monitor.
 */
export function useClickOutside<T extends HTMLElement = HTMLDivElement>(
  handler: () => void,
  enabled: boolean = true,
): React.RefObject<T> {
  const ref = useRef<T>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [handler, enabled]);

  return ref;
}
