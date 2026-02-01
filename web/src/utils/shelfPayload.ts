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

import type { Shelf, ShelfCreate, ShelfType, ShelfUpdate } from "@/types/shelf";

type ShelfSaveInput = ShelfCreate | ShelfUpdate;

interface BuildShelfCreatePayloadOptions {
  /**
   * Fallback name used when input payload does not include a name
   * (e.g., "create shelf" flows that start with a separate name textbox).
   */
  fallbackName?: string;
}

/**
 * Normalize shelf type and filter rules.
 *
 * Notes
 * -----
 * - Only `magic_shelf` should have `filter_rules` set.
 * - For other shelf types, `filter_rules` is forced to `null` to prevent stale
 *   rules persisting when switching types.
 */
function normalizeShelfTypeAndRules<
  T extends {
    shelf_type?: ShelfType | null;
    filter_rules?: Record<string, unknown> | null;
  },
>(payload: T): T {
  const shelfType = payload.shelf_type ?? null;

  if (shelfType === "magic_shelf") {
    return {
      ...payload,
      filter_rules: payload.filter_rules ?? null,
    };
  }

  return {
    ...payload,
    filter_rules: null,
  };
}

/**
 * Build a canonical `ShelfCreate` payload.
 *
 * Parameters
 * ----------
 * input : ShelfCreate | ShelfUpdate
 *     Incoming data from UI components (often `ShelfEditModal`) or wrapper flows.
 * options : BuildShelfCreatePayloadOptions, optional
 *     Options for fallback handling.
 *
 * Returns
 * -------
 * ShelfCreate
 *     A normalized create payload, preserving magic shelf fields when present.
 */
export function buildShelfCreatePayload(
  input: ShelfSaveInput,
  options: BuildShelfCreatePayloadOptions = {},
): ShelfCreate {
  const fallbackName = options.fallbackName ?? "";

  const name = (input.name ?? "").toString().trim() || fallbackName.trim() || "";

  const payload: ShelfCreate = {
    name,
    description: input.description ?? null,
    is_public: input.is_public ?? false,
    shelf_type: input.shelf_type ?? undefined,
    filter_rules: input.filter_rules ?? null,
  };

  return normalizeShelfTypeAndRules(payload);
}

/**
 * Build a canonical `ShelfUpdate` payload from a full `Shelf`.
 *
 * Parameters
 * ----------
 * shelf : Shelf
 *     Current shelf state to persist.
 *
 * Returns
 * -------
 * ShelfUpdate
 *     A normalized update payload that includes magic shelf rules when applicable.
 */
export function buildShelfUpdatePayloadFromShelf(shelf: Shelf): ShelfUpdate {
  const payload: ShelfUpdate = {
    name: shelf.name,
    description: shelf.description,
    is_public: shelf.is_public,
    shelf_type: shelf.shelf_type,
    filter_rules: shelf.filter_rules ?? null,
  };

  return normalizeShelfTypeAndRules(payload);
}

/**
 * Build a local UI patch from a full `Shelf`.
 *
 * Notes
 * -----
 * This is intentionally typed as `Partial<Shelf>` (not `ShelfUpdate`) so callers
 * can safely pass it to local state updaters without widening fields to nullable
 * types like `ShelfUpdate.name?: string | null`.
 */
export function buildShelfLocalPatchFromShelf(shelf: Shelf): Partial<Shelf> {
  const normalized = buildShelfUpdatePayloadFromShelf(shelf);

  return {
    // `Shelf` requires `name: string`; keep it non-null for local state.
    name: shelf.name,
    description: normalized.description ?? null,
    is_public: normalized.is_public ?? shelf.is_public,
    shelf_type: normalized.shelf_type ?? shelf.shelf_type,
    filter_rules: normalized.filter_rules ?? null,
  };
}
