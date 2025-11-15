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
 * Modal utility functions.
 *
 * Provides reusable functions for modal rendering and behavior.
 * Follows SRP by separating modal logic from presentation.
 * Follows DRY by centralizing modal patterns.
 */

import type { ReactNode } from "react";
import { createPortal } from "react-dom";

/**
 * Render modal content in a portal.
 *
 * Renders the provided content in a portal attached to document.body,
 * avoiding DOM hierarchy conflicts. Follows SRP by handling only portal rendering.
 *
 * Parameters
 * ----------
 * content : ReactNode
 *     Modal content to render.
 * container? : HTMLElement
 *     Portal container element (defaults to document.body).
 *
 * Returns
 * -------
 * ReactNode
 *     Portal-wrapped content.
 */
export function renderModalPortal(
  content: ReactNode,
  container: HTMLElement = document.body,
): ReactNode {
  return createPortal(content, container);
}
