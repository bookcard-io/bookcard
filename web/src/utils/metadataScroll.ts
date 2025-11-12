/**
 * Metadata scroll utility functions.
 *
 * Provides reusable functions for scrolling to metadata results.
 * Follows SRP by separating scroll logic from presentation.
 * Follows DRY by centralizing scroll behavior.
 */

import { normalizeProviderName } from "./metadata";

/**
 * Scroll to the first result of a specific provider.
 *
 * First scrolls to the results section container, then scrolls to
 * the specific provider's first result after a short delay.
 *
 * Parameters
 * ----------
 * providerName : string
 *     Provider display name to scroll to.
 */
export function scrollToProviderResults(providerName: string): void {
  // First, scroll to the results section container
  const resultsSection = document.getElementById("metadata-results-section");
  if (resultsSection) {
    resultsSection.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  // Then, after a short delay, scroll to the specific provider's first result
  // This ensures the results section is visible first
  setTimeout(() => {
    // Normalize provider name to match source_id format
    const sourceId = normalizeProviderName(providerName);
    const elementId = `result-${sourceId}`;
    const element = document.getElementById(elementId);

    if (element) {
      // Scroll to the element with smooth behavior
      element.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, 100);
}
