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
 * Font utilities for reading components.
 *
 * Centralized font face generation and font-related calculations.
 * Follows SRP by separating font logic from UI components.
 * Follows DRY by eliminating font generation duplication.
 */

/**
 * Generate @font-face CSS for all supported reading fonts.
 *
 * Returns
 * -------
 * string
 *     CSS string containing all @font-face declarations.
 */
export function generateFontFaces(): string {
  return `
    /* Bookerly */
    @font-face {
      font-family: "Bookerly";
      font-weight: 400;
      font-style: normal;
      src: url("/fonts/Bookerly-Regular.ttf") format("truetype");
    }
    @font-face {
      font-family: "Bookerly";
      font-weight: 400;
      font-style: italic;
      src: url("/fonts/Bookerly-Italic.ttf") format("truetype");
    }
    @font-face {
      font-family: "Bookerly";
      font-weight: 700;
      font-style: normal;
      src: url("/fonts/Bookerly-Bold.ttf") format("truetype");
    }
    @font-face {
      font-family: "Bookerly";
      font-weight: 700;
      font-style: italic;
      src: url("/fonts/Bookerly-BoldItalic.ttf") format("truetype");
    }

    /* Amazon Ember */
    @font-face {
      font-family: "Amazon Ember";
      font-weight: 400;
      font-style: normal;
      src: url("/fonts/AmazonEmber_Rg.ttf") format("truetype");
    }
    @font-face {
      font-family: "Amazon Ember";
      font-weight: 400;
      font-style: italic;
      src: url("/fonts/AmazonEmber_RgIt.ttf") format("truetype");
    }
    @font-face {
      font-family: "Amazon Ember";
      font-weight: 700;
      font-style: normal;
      src: url("/fonts/AmazonEmber_Bd.ttf") format("truetype");
    }
    @font-face {
      font-family: "Amazon Ember";
      font-weight: 700;
      font-style: italic;
      src: url("/fonts/AmazonEmber_BdIt.ttf") format("truetype");
    }

    /* OpenDyslexic */
    @font-face {
      font-family: "OpenDyslexic";
      font-weight: 400;
      font-style: normal;
      src: url("/fonts/opendyslexic-latin-400-normal.woff2") format("woff2");
    }
    @font-face {
      font-family: "OpenDyslexic";
      font-weight: 400;
      font-style: italic;
      src: url("/fonts/opendyslexic-latin-400-italic.woff2") format("woff2");
    }

    /* Literata */
    @font-face {
      font-family: "Literata";
      font-weight: 400;
      font-style: normal;
      src: url("/fonts/literata-latin-400-normal.woff2") format("woff2");
    }
    @font-face {
      font-family: "Literata";
      font-weight: 400;
      font-style: italic;
      src: url("/fonts/literata-latin-400-italic.woff2") format("woff2");
    }
    @font-face {
      font-family: "Literata";
      font-weight: 400;
      font-style: normal;
      unicode-range: U+0370-03FF;
      src: url("/fonts/literata-greek-400-normal.woff2") format("woff2");
    }
    @font-face {
      font-family: "Literata";
      font-weight: 400;
      font-style: italic;
      unicode-range: U+0370-03FF;
      src: url("/fonts/literata-greek-400-italic.woff2") format("woff2");
    }
    @font-face {
      font-family: "Literata";
      font-weight: 400;
      font-style: normal;
      unicode-range: U+0400-04FF;
      src: url("/fonts/literata-cyrillic-400-normal.woff2") format("woff2");
    }
    @font-face {
      font-family: "Literata";
      font-weight: 400;
      font-style: italic;
      unicode-range: U+0400-04FF;
      src: url("/fonts/literata-cyrillic-400-italic.woff2") format("woff2");
    }
    @font-face {
      font-family: "Literata";
      font-weight: 400;
      font-style: normal;
      unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+1EA0-1EF9, U+20AB;
      src: url("/fonts/literata-vietnamese-400-normal.woff2") format("woff2");
    }
    @font-face {
      font-family: "Literata";
      font-weight: 400;
      font-style: italic;
      unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+1EA0-1EF9, U+20AB;
      src: url("/fonts/literata-vietnamese-400-italic.woff2") format("woff2");
    }
  `;
}

/**
 * Convert font size in pixels to percentage for EPUB themes.
 *
 * Parameters
 * ----------
 * fontSizePx : number
 *     Font size in pixels.
 * baseFontSizePx : number
 *     Base font size in pixels (default: 16).
 *
 * Returns
 * -------
 * string
 *     Font size as percentage string (e.g., "100%").
 */
export function fontSizeToPercent(
  fontSizePx: number,
  baseFontSizePx: number = 16,
): string {
  return `${(fontSizePx / baseFontSizePx) * 100}%`;
}
