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
import { fetchPermissions, type Permission } from "@/services/roleService";
import type { SearchSuggestionItem } from "@/types/search";

export interface UsePermissionSuggestionsResult {
  /** List of permission suggestions. */
  suggestions: SearchSuggestionItem[];
  /** Whether suggestions are currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** All available permissions. */
  permissions: Permission[];
}

/**
 * Custom hook for fetching and filtering permission suggestions.
 *
 * Follows SRP by separating permission suggestion logic from UI components.
 *
 * Parameters
 * ----------
 * query : string
 *     Search query string to filter permissions.
 * enabled : boolean
 *     Whether to fetch suggestions (default: true).
 *
 * Returns
 * -------
 * UsePermissionSuggestionsResult
 *     Permission suggestions data.
 */
export function usePermissionSuggestions(
  query: string,
  enabled: boolean = true,
): UsePermissionSuggestionsResult {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasFetchedRef = useRef(false);

  // Fetch all permissions once (avoid duplicate fetches in React StrictMode)
  useEffect(() => {
    if (!enabled || hasFetchedRef.current) {
      return;
    }

    const loadPermissions = async () => {
      hasFetchedRef.current = true;
      setIsLoading(true);
      setError(null);
      try {
        const fetchedPermissions = await fetchPermissions();
        setPermissions(fetchedPermissions);
        // If no permissions were fetched and it's not an error, that's okay
        // (endpoint may not be implemented yet)
        if (fetchedPermissions.length === 0) {
          setError(null); // Don't show error for empty results
        }
      } catch (err) {
        // This shouldn't happen now since fetchPermissions returns empty array on error
        // But keep this for safety
        const message =
          err instanceof Error ? err.message : "Failed to fetch permissions";
        setError(message);
        console.warn("Failed to fetch permissions:", err);
        hasFetchedRef.current = false; // Allow retry on error
      } finally {
        setIsLoading(false);
      }
    };

    void loadPermissions();
  }, [enabled]);

  // Filter permissions based on query
  const suggestions = useCallback((): SearchSuggestionItem[] => {
    if (!query.trim()) {
      return permissions.map((permission) => ({
        id: permission.id,
        name: permission.name,
      }));
    }

    const queryLower = query.toLowerCase();
    return permissions
      .filter(
        (permission) =>
          permission.name.toLowerCase().includes(queryLower) ||
          permission.resource.toLowerCase().includes(queryLower) ||
          permission.action.toLowerCase().includes(queryLower),
      )
      .map((permission) => ({
        id: permission.id,
        name: permission.name,
      }));
  }, [query, permissions]);

  return {
    suggestions: suggestions(),
    isLoading,
    error,
    permissions,
  };
}
