import { useEffect, useRef, useState } from "react";

/**
 * Custom hook for debouncing values.
 *
 * Delays updating the debounced value until after the specified delay
 * has passed since the last time the source value changed.
 *
 * Parameters
 * ----------
 * value : T
 *     The value to debounce.
 * delay : number
 *     The delay in milliseconds (default: 300).
 *
 * Returns
 * -------
 * T
 *     The debounced value.
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [value, delay]);

  return debouncedValue;
}
