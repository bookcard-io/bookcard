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
 * Genre and style categorization utilities.
 *
 * Categorizes book subjects into high-level genres and specific styles,
 * similar to Plex's genre/style system for music.
 * Follows SRP by focusing solely on categorization logic.
 */

/**
 * High-level genre categories.
 * These are the top-level classifications (like "Pop/Rock" in music).
 * Stored in lowercase for case-insensitive matching.
 */
const GENRE_CATEGORIES = new Set([
  // Fiction genres
  "fiction",
  "nonfiction",
  "non-fiction",
  "poetry",
  "drama",
  "literary collections",
  "literature",
  // Age categories (can be genres)
  "young adult",
  "adult",
  "juvenile fiction",
  "children's fiction",
  "children's stories",
  // Format categories
  "comic books",
  "graphic novels",
  "short stories",
  "novella",
]);

/**
 * Genre keywords that indicate a high-level genre.
 * These are patterns that suggest a genre rather than a style.
 */
const GENRE_KEYWORDS = [
  /^fiction$/i,
  /^nonfiction$/i,
  /^non-fiction$/i,
  /^poetry$/i,
  /^drama$/i,
  /^literature$/i,
  /^literary collections$/i,
  /^young adult$/i,
  /^juvenile fiction$/i,
  /^children's fiction$/i,
  /^children's stories$/i,
  /^comic books$/i,
  /^graphic novels$/i,
  /^short stories$/i,
  /^novella$/i,
];

/**
 * Style categories that should be treated as genres.
 * These are broad enough to be considered genres (like "Pop/Rock" in music).
 * Stored in lowercase for case-insensitive matching.
 */
const BROAD_STYLES_AS_GENRES = new Set([
  // Fiction styles that are broad enough to be genres
  "fantasy",
  "science fiction",
  "mystery",
  "thriller",
  "romance",
  "horror",
  "historical fiction",
  "adventure",
  "action & adventure",
  "action and adventure",
  "suspense",
  "crime",
  "western",
  // Nonfiction styles that are broad enough to be genres
  "biography",
  "history",
  "autobiography",
  "memoir",
  "self-help",
  "philosophy",
  "religion",
  "politics",
  "economics",
  "science",
  "technology",
  "art",
  "music",
  "travel",
  "cooking",
  "health",
  "education",
  "psychology",
  "sociology",
  "business",
  "law",
]);

/**
 * Known style patterns that are acceptable as styles.
 * These are specific subcategories (like "Epic Fantasy", "Hard Science Fiction").
 * Uses regex patterns for flexible matching.
 */
const KNOWN_STYLE_PATTERNS = [
  // Fantasy subgenres
  /^epic\s+fantasy$/i,
  /^high\s+fantasy$/i,
  /^urban\s+fantasy$/i,
  /^dark\s+fantasy$/i,
  /^epic$/i,
  // Science fiction subgenres
  /^hard\s+science\s+fiction$/i,
  /^hard\s+sci-fi$/i,
  /^hard\s+science-fiction$/i,
  /^sci-fi$/i,
  /^science-fiction$/i,
  /^space\s+opera$/i,
  /^cyberpunk$/i,
  /^dystopian$/i,
  /^dystopias$/i,
  // Age-based styles
  /^coming-of-age$/i,
  /^coming\s+of\s+age$/i,
  // Thematic styles
  /^magic$/i,
  /^intrigue$/i,
  /^revolution$/i,
  /^prophecy$/i,
  /^survival$/i,
  // Format/styles
  /^graphic\s+novel$/i,
  /^short\s+stories$/i,
  /^adventure\s+stories$/i,
  // Thriller subgenres
  /^psychological\s+thriller$/i,
  /^suspense\s+fiction$/i,
  // Horror subgenres
  /^gothic$/i,
  /^supernatural$/i,
  // Romance subgenres
  /^romantic\s+comedy$/i,
  /^contemporary\s+romance$/i,
  // Mystery subgenres
  /^detective$/i,
  /^noir$/i,
  // Literary styles
  /^literary\s+fiction$/i,
  /^classic\s+literature$/i,
  /^classics$/i,
  /^absurdist$/i,
  /^psychological\s+fiction$/i,
  /^political\s+fiction$/i,
  /^satire$/i,
  /^parody$/i,
  /^humor$/i,
  /^humorous$/i,
  // Historical styles
  /^regency$/i,
  // Social/psychological styles
  /^social\s+psychology$/i,
  /^ethics$/i,
];

/**
 * Categorization result.
 */
export interface GenreStyleCategorization {
  /** High-level genres (e.g., "Fiction", "Nonfiction"). */
  genres: string[];
  /** Specific styles (e.g., "Epic Fantasy", "Hard Science Fiction"). */
  styles: string[];
}

/**
 * Categorize subjects into genres and styles.
 *
 * Genres are high-level categories (Fiction, Nonfiction, etc.).
 * Styles are more specific subcategories (Epic Fantasy, Hard Science Fiction, etc.).
 *
 * Parameters
 * ----------
 * subjects : string[]
 *     Array of subject strings to categorize.
 *
 * Returns
 * -------
 * GenreStyleCategorization
 *     Object with separated genres and styles arrays.
 *
 * Examples
 * --------
 * >>> categorizeGenresAndStyles(["Fiction", "Fantasy", "Epic Fantasy", "Magic"])
 * { genres: ["Fiction", "Fantasy"], styles: ["Epic Fantasy", "Magic"] }
 */
export function categorizeGenresAndStyles(
  subjects: string[],
): GenreStyleCategorization {
  const genres: string[] = [];
  const styles: string[] = [];
  const seen = new Set<string>();

  for (const subject of subjects) {
    // Skip duplicates (case-insensitive)
    const subjectLower = subject.toLowerCase();
    if (seen.has(subjectLower)) {
      continue;
    }
    seen.add(subjectLower);

    // Skip metadata/subject tags that aren't useful for display
    // (e.g., "New York Times bestseller", series names, etc.)
    if (
      subjectLower.startsWith("nyt:") ||
      subjectLower.startsWith("series:") ||
      subjectLower.includes("new york times") ||
      subjectLower.includes("bestseller") ||
      subjectLower.includes("reviewed") ||
      subjectLower.includes("collection:") ||
      subjectLower.includes("award") ||
      subjectLower.includes("lambda literary")
    ) {
      continue;
    }

    // Check if it's a high-level genre (case-insensitive)
    const isGenre =
      GENRE_CATEGORIES.has(subjectLower) ||
      GENRE_KEYWORDS.some((pattern) => pattern.test(subject)) ||
      BROAD_STYLES_AS_GENRES.has(subjectLower);

    if (isGenre) {
      // Preserve original casing for display
      genres.push(subject);
    } else {
      // Only include as style if it matches a known style pattern
      const matchesStylePattern = KNOWN_STYLE_PATTERNS.some((pattern) =>
        pattern.test(subject),
      );
      if (matchesStylePattern) {
        styles.push(subject);
      }
      // Otherwise, skip it (it's likely a book title, character name, or other noise)
    }
  }

  // Sort for consistent display
  genres.sort();
  styles.sort();

  return { genres, styles };
}

/**
 * Get primary genre from subjects.
 *
 * Returns the most prominent genre, or null if none found.
 *
 * Parameters
 * ----------
 * subjects : string[]
 *     Array of subject strings.
 *
 * Returns
 * -------
 * string | null
 *     Primary genre, or null if none found.
 */
export function getPrimaryGenre(subjects: string[]): string | null {
  const { genres } = categorizeGenresAndStyles(subjects);
  // Prefer "Fiction" or "Nonfiction" as primary (case-insensitive)
  const fictionGenre = genres.find((g) => g.toLowerCase() === "fiction");
  if (fictionGenre) {
    return fictionGenre; // Preserve original casing
  }
  const nonfictionGenre = genres.find(
    (g) =>
      g.toLowerCase() === "nonfiction" || g.toLowerCase() === "non-fiction",
  );
  if (nonfictionGenre) {
    return nonfictionGenre; // Preserve original casing
  }
  // Otherwise return first genre
  return genres[0] || null;
}
