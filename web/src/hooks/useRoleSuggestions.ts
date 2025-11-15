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

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchRoles, type Role } from "@/services/roleService";
import type { SearchSuggestionItem } from "@/types/search";

export interface UseRoleSuggestionsResult {
  /** List of role suggestions. */
  suggestions: SearchSuggestionItem[];
  /** Whether suggestions are currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** All available roles. */
  roles: Role[];
}

/**
 * Custom hook for fetching and filtering role suggestions.
 *
 * Follows SRP by separating role suggestion logic from UI components.
 *
 * Parameters
 * ----------
 * query : string
 *     Search query string to filter roles.
 * enabled : boolean
 *     Whether to fetch suggestions (default: true).
 *
 * Returns
 * -------
 * UseRoleSuggestionsResult
 *     Role suggestions data.
 */
export function useRoleSuggestions(
  query: string,
  enabled: boolean = true,
): UseRoleSuggestionsResult {
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasFetchedRef = useRef(false);

  // Fetch all roles once (avoid duplicate fetches in React StrictMode)
  useEffect(() => {
    if (!enabled || hasFetchedRef.current) {
      return;
    }

    const loadRoles = async () => {
      hasFetchedRef.current = true;
      setIsLoading(true);
      setError(null);
      try {
        const fetchedRoles = await fetchRoles();
        setRoles(fetchedRoles);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to fetch roles";
        setError(message);
        console.error("Failed to fetch roles:", err);
        hasFetchedRef.current = false; // Allow retry on error
      } finally {
        setIsLoading(false);
      }
    };

    void loadRoles();
  }, [enabled]);

  // Filter roles based on query
  const suggestions = useCallback((): SearchSuggestionItem[] => {
    if (!query.trim()) {
      return roles.map((role) => ({
        id: role.id,
        name: role.name,
      }));
    }

    const queryLower = query.toLowerCase();
    return roles
      .filter((role) => role.name.toLowerCase().includes(queryLower))
      .map((role) => ({
        id: role.id,
        name: role.name,
      }));
  }, [query, roles]);

  return {
    suggestions: suggestions(),
    isLoading,
    error,
    roles,
  };
}
