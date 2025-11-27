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
 * Configuration constants for user preferences.
 *
 * Centralized location for available options.
 * Follows SOC by separating data from components.
 */

export const AVAILABLE_LANGUAGES = [
  "English",
  "Spanish",
  "French",
  "German",
  "Italian",
  "Portuguese",
  "Chinese",
  "Japanese",
  "Korean",
] as const;

export const AVAILABLE_METADATA_PROVIDERS = [
  "Hardcover",
  "Google Books",
  "Amazon",
  "豆瓣",
  "Google Scholar",
  "LubimyCzytac.pl",
  "ComicVine",
  "OpenLibrary",
] as const;

export const DISPLAY_MODE_OPTIONS = [
  { value: "pagination", label: "Use pagination" },
  { value: "infinite-scroll", label: "Use infinite scroll" },
] as const;

export const SORT_FIELD_OPTIONS = [
  { value: "timestamp", label: "Added date" },
  { value: "title", label: "Title" },
  { value: "author_sort", label: "Author" },
  { value: "pubdate", label: "Modified date" },
  { value: "series_index", label: "Size" },
] as const;

export const SORT_ORDER_OPTIONS = [
  { value: "asc", label: "Ascending" },
  { value: "desc", label: "Descending" },
] as const;

export const PAGE_SIZE_OPTIONS = [
  { value: "10", label: "10" },
  { value: "20", label: "20" },
  { value: "30", label: "30" },
  { value: "50", label: "50" },
  { value: "100", label: "100" },
] as const;

export const VIEW_MODE_OPTIONS = [
  { value: "grid", label: "Grid" },
  { value: "list", label: "List" },
] as const;

export const BOOK_DETAILS_OPEN_MODE_OPTIONS = [
  { value: "modal", label: "Open in modal" },
  { value: "page", label: "Navigate to page" },
] as const;

export const THEME_PREFERENCE_OPTIONS = [
  { value: "dark", label: "Dark theme" },
  { value: "light", label: "Light theme" },
] as const;

export const METADATA_DOWNLOAD_FORMAT_OPTIONS = [
  { value: "opf", label: "OPF" },
  { value: "json", label: "JSON" },
  { value: "yaml", label: "YAML" },
] as const;

export const CONVERSION_TARGET_FORMAT_OPTIONS = [
  { value: "epub", label: "EPUB" },
  { value: "mobi", label: "MOBI" },
  { value: "azw3", label: "AZW3" },
  { value: "kepub", label: "KEPUB" },
  { value: "pdf", label: "PDF" },
] as const;

export const SUPPORTED_BOOK_FORMATS = [
  { value: "epub", label: "EPUB" },
  { value: "mobi", label: "MOBI" },
  { value: "azw3", label: "AZW3" },
  { value: "azw", label: "AZW" },
  { value: "azw4", label: "AZW4" },
  { value: "kepub", label: "KEPUB" },
  { value: "pdf", label: "PDF" },
  { value: "fb2", label: "FB2" },
  { value: "html", label: "HTML" },
  { value: "htmlz", label: "HTMLZ" },
  { value: "txt", label: "TXT" },
  { value: "txtz", label: "TXTZ" },
  { value: "rtf", label: "RTF" },
  { value: "lit", label: "LIT" },
  { value: "lrf", label: "LRF" },
  { value: "odt", label: "ODT" },
  { value: "docx", label: "DOCX" },
  { value: "cbz", label: "CBZ" },
  { value: "cbr", label: "CBR" },
  { value: "cb7", label: "CB7" },
  { value: "cbc", label: "CBC" },
  { value: "chm", label: "CHM" },
  { value: "djvu", label: "DJVU" },
  { value: "prc", label: "PRC" },
  { value: "pdb", label: "PDB" },
  { value: "pml", label: "PML" },
  { value: "rb", label: "RB" },
  { value: "snb", label: "SNB" },
  { value: "tcr", label: "TCR" },
] as const;

export const THEME_PREFERENCE_SETTING_KEY = "theme_preference";

export const READING_FONT_FAMILY_SETTING_KEY = "reading_font_family";
export const READING_FONT_SIZE_SETTING_KEY = "reading_font_size";
export const READING_PAGE_COLOR_SETTING_KEY = "reading_page_color";
export const READING_PAGE_LAYOUT_SETTING_KEY = "reading_page_layout";

export const ENABLED_METADATA_PROVIDERS_SETTING_KEY =
  "enabled_metadata_providers";

export const AUTO_CONVERT_ON_IMPORT_SETTING_KEY = "auto_convert_on_import";
export const AUTO_CONVERT_TARGET_FORMAT_SETTING_KEY =
  "auto_convert_target_format";
export const AUTO_CONVERT_IGNORED_FORMATS_SETTING_KEY =
  "auto_convert_ignored_formats";
export const AUTO_CONVERT_BACKUP_ORIGINALS_SETTING_KEY =
  "auto_convert_backup_originals";

export const DEFAULT_ENABLED_METADATA_PROVIDERS = [
  "Hardcover",
  "Google Books",
  "Amazon",
] as const;

/**
 * Gets the label for the theme toggle button.
 *
 * Returns the label for the opposite theme (the theme that will be activated
 * when the toggle is clicked).
 *
 * Parameters
 * ----------
 * currentTheme : "dark" | "light"
 *     The current theme.
 *
 * Returns
 * -------
 * string
 *     The label for the toggle button.
 */
export function getToggleThemeLabel(currentTheme: "dark" | "light"): string {
  const oppositeTheme = currentTheme === "dark" ? "light" : "dark";
  const option = THEME_PREFERENCE_OPTIONS.find(
    (opt) => opt.value === oppositeTheme,
  );
  return option?.label ?? "Theme";
}
