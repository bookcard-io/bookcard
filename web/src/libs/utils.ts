import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge class names with Tailwind class conflict resolution.
 *
 * Combines clsx for conditional classes and tailwind-merge to resolve
 * Tailwind class conflicts (e.g., "p-4 p-2" becomes "p-2").
 *
 * Parameters
 * ----------
 * ...inputs : ClassValue[]
 *     Class names to merge (strings, objects, arrays, etc.).
 *
 * Returns
 * -------
 * string
 *     Merged class name string.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
