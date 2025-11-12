// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
