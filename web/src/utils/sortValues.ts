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
 * Sort value generation utilities.
 *
 * Provides functions for generating author_sort and title_sort values.
 * Follows SRP by separating sort value generation logic from presentation.
 * Follows DRY by centralizing sort value generation.
 */

/**
 * Default list of titles/prefixes to ignore when generating author_sort.
 *
 * Common academic and professional titles that should not be considered
 * as part of the last name for sorting purposes.
 */
const DEFAULT_IGNORED_TITLES = [
  "PhD",
  "Ph.D",
  "Ph.D.",
  "BE",
  "B.E",
  "B.E.",
  "BS",
  "B.S",
  "B.S.",
  "BA",
  "B.A",
  "B.A.",
  "MA",
  "M.A",
  "M.A.",
  "MS",
  "M.S",
  "M.S.",
  "MBA",
  "M.B.A",
  "M.B.A.",
  "MD",
  "M.D",
  "M.D.",
  "JD",
  "J.D",
  "J.D.",
  "Esq",
  "Esq.",
  "Jr",
  "Jr.",
  "Sr",
  "Sr.",
  "II",
  "III",
  "IV",
  "V",
  "VI",
  "VII",
  "VIII",
  "IX",
  "X",
  // British honors and knight titles
  "OBE",
  "O.B.E",
  "O.B.E.",
  "MBE",
  "M.B.E",
  "M.B.E.",
  "CBE",
  "C.B.E",
  "C.B.E.",
  "KBE",
  "K.B.E",
  "K.B.E.",
  "DBE",
  "D.B.E",
  "D.B.E.",
  "GBE",
  "G.B.E",
  "G.B.E.",
  "KCMG",
  "K.C.M.G",
  "K.C.M.G.",
  "DCMG",
  "D.C.M.G",
  "D.C.M.G.",
  "GCMG",
  "G.C.M.G",
  "G.C.M.G.",
  "KCVO",
  "K.C.V.O",
  "K.C.V.O.",
  "DCVO",
  "D.C.V.O",
  "D.C.V.O.",
  "GCVO",
  "G.C.V.O",
  "G.C.V.O.",
];

/**
 * Default list of articles to ignore when generating title_sort.
 *
 * Common articles that should be removed from the beginning of titles
 * for sorting purposes.
 */
const DEFAULT_ARTICLES = ["a", "an", "the"];

/**
 * Generate author_sort value from author name(s).
 *
 * Extracts the last name (ignoring titles) and formats as "Last, First".
 * For multiple authors, uses the first author's name.
 * The sorting value is the most immediate last value before any spaces,
 * or the sole value if there's only one word.
 *
 * Parameters
 * ----------
 * authorNames : string[] | null | undefined
 *     Array of author names. If multiple, uses the first author.
 * ignoredTitles? : string[]
 *     Optional list of titles to ignore (defaults to DEFAULT_IGNORED_TITLES).
 *
 * Returns
 * -------
 * string | null
 *     Generated author_sort value (e.g., "Smith, Adam") or null if no authors.
 */
export function generateAuthorSort(
  authorNames: string[] | null | undefined,
  ignoredTitles: string[] = DEFAULT_IGNORED_TITLES,
): string | null {
  if (!authorNames || authorNames.length === 0) {
    return null;
  }

  // Use first author for sort value
  const firstAuthor = authorNames[0];
  if (!firstAuthor) {
    return null;
  }
  const authorName = firstAuthor.trim();
  if (!authorName) {
    return null;
  }

  // Split by spaces and filter out ignored titles
  const parts = authorName.split(/\s+/).filter((part) => {
    const normalizedPart = part.replace(/[.,]/g, "").toUpperCase();
    return !ignoredTitles.some(
      (title) => normalizedPart === title.replace(/[.,]/g, "").toUpperCase(),
    );
  });

  if (parts.length === 0) {
    return null;
  }

  // If only one part, use it as-is
  if (parts.length === 1) {
    const singlePart = parts[0];
    return singlePart ?? null;
  }

  // Get the last part as the surname
  const lastName = parts[parts.length - 1];
  // Get all parts except the last as the first name(s)
  const firstName = parts.slice(0, -1).join(" ");

  // Format as "Last, First"
  return `${lastName}, ${firstName}`;
}

/**
 * Generate title_sort value from title.
 *
 * Removes articles (a, an, the) from the beginning of the title
 * for sorting purposes.
 *
 * Parameters
 * ----------
 * title : string | null | undefined
 *     Book title.
 * articles? : string[]
 *     Optional list of articles to ignore (defaults to DEFAULT_ARTICLES).
 *
 * Returns
 * -------
 * string | null
 *     Generated title_sort value or null if no title.
 */
export function generateTitleSort(
  title: string | null | undefined,
  articles: string[] = DEFAULT_ARTICLES,
): string | null {
  if (!title || !title.trim()) {
    return null;
  }

  const trimmedTitle = title.trim();

  // Check if title starts with an article (case-insensitive)
  const lowerTitle = trimmedTitle.toLowerCase();
  for (const article of articles) {
    if (!article) {
      continue;
    }
    // Match article at the start, followed by a space or comma
    const articleRegex = new RegExp(`^${article}\\s+`, "i");
    if (articleRegex.test(lowerTitle)) {
      // Remove the article and following space
      const result = trimmedTitle.replace(articleRegex, "").trim();
      return result || null;
    }
  }

  // No article found, return title as-is
  return trimmedTitle || null;
}
