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

"use client";

import { useEffect, useRef, useState } from "react";
import type { SearchSuggestionItem } from "@/types/search";
import { createEmptyFilters } from "@/utils/filters";
import { FilterInput } from "./FilterInput";

export interface FilterValues {
  authorIds: number[];
  titleIds: number[];
  genreIds: number[];
  publisherIds: number[];
  identifierIds: number[];
  seriesIds: number[];
  formats: string[];
  ratingIds: number[];
  languageIds: number[];
}

export interface SelectedFilterSuggestions {
  authorIds?: SearchSuggestionItem[];
  titleIds?: SearchSuggestionItem[];
  genreIds?: SearchSuggestionItem[];
  publisherIds?: SearchSuggestionItem[];
  identifierIds?: SearchSuggestionItem[];
  seriesIds?: SearchSuggestionItem[];
  formats?: SearchSuggestionItem[];
  ratingIds?: SearchSuggestionItem[];
  languageIds?: SearchSuggestionItem[];
}

export interface FiltersPanelProps {
  /**
   * Current filter values.
   */
  filters?: FilterValues;
  /**
   * Selected filter suggestions (for display names).
   */
  selectedSuggestions?: SelectedFilterSuggestions;
  /**
   * Callback fired when filters change.
   */
  onFiltersChange?: (filters: FilterValues) => void;
  /**
   * Callback fired when selected suggestions change.
   */
  onSuggestionsChange?: (suggestions: SelectedFilterSuggestions) => void;
  /**
   * Callback fired when Apply Filter button is clicked.
   */
  onApply?: (filters: FilterValues) => void;
  /**
   * Callback fired when Clear Filters button is clicked.
   */
  onClear?: () => void;
  /**
   * Callback fired when the panel should be closed.
   */
  onClose?: () => void;
}

/**
 * Filters panel component with all filter inputs.
 *
 * Displays a grid of filter inputs for author, title, genre, publisher,
 * identifier, series, format, rating, and language.
 *
 * Follows SRP by handling only filter UI and state management.
 */
export function FiltersPanel({
  filters = createEmptyFilters(),
  selectedSuggestions: initialSelectedSuggestions = {},
  onFiltersChange,
  onSuggestionsChange,
  onApply,
  onClear,
  onClose,
}: FiltersPanelProps) {
  const [selectedSuggestions, setSelectedSuggestions] =
    useState<SelectedFilterSuggestions>(initialSelectedSuggestions);

  const panelRef = useRef<HTMLDivElement>(null);

  // Sync selectedSuggestions when initialSelectedSuggestions changes (panel reopened)
  useEffect(() => {
    setSelectedSuggestions(initialSelectedSuggestions);
  }, [initialSelectedSuggestions]);

  // Handle click outside to close panel
  // Exclude clicks on the FiltersButton
  useEffect(() => {
    if (!onClose) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;

      // Don't close if clicking on the FiltersButton or its children
      const isFiltersButton = target.closest("[data-filters-button]");
      if (isFiltersButton) {
        return;
      }

      // Don't close if clicking inside the panel
      if (panelRef.current?.contains(target)) {
        return;
      }

      // Close if clicking outside
      onClose();
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [onClose]);

  const handleFilterChange = (
    filterKey: keyof FilterValues,
    ids: number[],
    suggestion?: SearchSuggestionItem,
  ) => {
    const newFilters = { ...filters };
    if (filterKey === "formats") {
      // Formats are strings, not IDs - this needs special handling
      // For now, we'll handle it separately
      return;
    }
    newFilters[filterKey] = ids as never;
    onFiltersChange?.(newFilters);

    // Update selected suggestions
    if (suggestion) {
      const updated = {
        ...selectedSuggestions,
        [filterKey]: [
          ...(selectedSuggestions[
            filterKey as keyof SelectedFilterSuggestions
          ] || []),
          suggestion,
        ],
      };
      setSelectedSuggestions(updated);
      onSuggestionsChange?.(updated);
    } else {
      // When removing items, update suggestions to match the new IDs
      const updated = {
        ...selectedSuggestions,
        [filterKey]: (
          selectedSuggestions[filterKey as keyof SelectedFilterSuggestions] as
            | SearchSuggestionItem[]
            | undefined
        )?.filter((s) => ids.includes(s.id)),
      };
      setSelectedSuggestions(updated);
      onSuggestionsChange?.(updated);
    }
  };

  const handleFormatChange = (formats: string[]) => {
    const newFilters = { ...filters, formats };
    onFiltersChange?.(newFilters);
  };

  const handleApply = () => {
    onApply?.(filters);
    onClose?.();
  };

  const handleClear = () => {
    // Clear all filters
    const emptyFilters = createEmptyFilters();
    onFiltersChange?.(emptyFilters);
    onSuggestionsChange?.({});
    onClear?.();
    onClose?.();
  };

  return (
    <div
      className="absolute top-[calc(100%-8px)] right-8 left-8 z-[100] flex flex-col rounded-xl border border-surface-a20 bg-surface-tonal-a10 shadow-[var(--shadow-card-hover)]"
      ref={panelRef}
    >
      <div className="flex items-center justify-between border-surface-a20 border-b p-4 px-6">
        <h2 className="m-0 font-semibold text-base text-text-a0">Filters</h2>
        {onClose && (
          <button
            type="button"
            className="flex h-8 w-8 items-center justify-center rounded-md border-none bg-transparent p-0 text-2xl text-text-a30 leading-none transition-[background-color_0.15s,color_0.15s] hover:bg-surface-tonal-a20 hover:text-text-a0"
            onClick={onClose}
            aria-label="Close filters"
          >
            ×
          </button>
        )}
      </div>
      <div className="grid grid-cols-3 gap-5 p-5 px-6">
        <FilterInput
          label="Author"
          filterType="author"
          value={filters.authorIds}
          selectedSuggestions={selectedSuggestions.authorIds || []}
          onChange={(ids) => handleFilterChange("authorIds", ids)}
          onSuggestionClick={(suggestion) => {
            handleFilterChange(
              "authorIds",
              [...filters.authorIds, suggestion.id],
              suggestion,
            );
          }}
        />
        <FilterInput
          label="Title"
          filterType="title"
          value={filters.titleIds}
          selectedSuggestions={selectedSuggestions.titleIds || []}
          onChange={(ids) => handleFilterChange("titleIds", ids)}
          onSuggestionClick={(suggestion) => {
            handleFilterChange(
              "titleIds",
              [...filters.titleIds, suggestion.id],
              suggestion,
            );
          }}
        />
        <FilterInput
          label="Genre"
          filterType="genre"
          value={filters.genreIds}
          selectedSuggestions={selectedSuggestions.genreIds || []}
          onChange={(ids) => handleFilterChange("genreIds", ids)}
          onSuggestionClick={(suggestion) => {
            handleFilterChange(
              "genreIds",
              [...filters.genreIds, suggestion.id],
              suggestion,
            );
          }}
        />
        <FilterInput
          label="Publisher"
          filterType="publisher"
          value={filters.publisherIds}
          selectedSuggestions={selectedSuggestions.publisherIds || []}
          onChange={(ids) => handleFilterChange("publisherIds", ids)}
          onSuggestionClick={(suggestion) => {
            handleFilterChange(
              "publisherIds",
              [...filters.publisherIds, suggestion.id],
              suggestion,
            );
          }}
        />
        <FilterInput
          label="Identifier (ISBN, ASIN, etc.)"
          filterType="identifier"
          value={filters.identifierIds}
          selectedSuggestions={selectedSuggestions.identifierIds || []}
          onChange={(ids) => handleFilterChange("identifierIds", ids)}
          onSuggestionClick={(suggestion) => {
            handleFilterChange(
              "identifierIds",
              [...filters.identifierIds, suggestion.id],
              suggestion,
            );
          }}
        />
        <FilterInput
          label="Series"
          filterType="series"
          value={filters.seriesIds}
          selectedSuggestions={selectedSuggestions.seriesIds || []}
          onChange={(ids) => handleFilterChange("seriesIds", ids)}
          onSuggestionClick={(suggestion) => {
            handleFilterChange(
              "seriesIds",
              [...filters.seriesIds, suggestion.id],
              suggestion,
            );
          }}
        />
        <FilterInput
          label="Format"
          filterType="format"
          value={filters.formats.map((_f, idx) => idx + 1)}
          selectedSuggestions={filters.formats.map((f, idx) => ({
            id: idx + 1,
            name: f,
          }))}
          onChange={(ids) => {
            // Convert IDs back to format strings
            const currentFormats = filters.formats;
            const newFormats = ids
              .map((id) => {
                // Find format by index (id - 1)
                return currentFormats[id - 1];
              })
              .filter((f): f is string => !!f);
            handleFormatChange(newFormats);
          }}
          onSuggestionClick={(suggestion) => {
            if (!filters.formats.includes(suggestion.name)) {
              handleFormatChange([...filters.formats, suggestion.name]);
              const updated = {
                ...selectedSuggestions,
                formats: [...(selectedSuggestions.formats || []), suggestion],
              };
              setSelectedSuggestions(updated);
              onSuggestionsChange?.(updated);
            }
          }}
        />
        <FilterInput
          label="Rating"
          filterType="rating"
          value={filters.ratingIds}
          selectedSuggestions={selectedSuggestions.ratingIds || []}
          onChange={(ids) => handleFilterChange("ratingIds", ids)}
          onSuggestionClick={(suggestion) => {
            handleFilterChange(
              "ratingIds",
              [...filters.ratingIds, suggestion.id],
              suggestion,
            );
          }}
        />
        <FilterInput
          label="Language"
          filterType="language"
          value={filters.languageIds}
          selectedSuggestions={selectedSuggestions.languageIds || []}
          onChange={(ids) => handleFilterChange("languageIds", ids)}
          onSuggestionClick={(suggestion) => {
            handleFilterChange(
              "languageIds",
              [...filters.languageIds, suggestion.id],
              suggestion,
            );
          }}
        />
      </div>
      <div className="flex items-center justify-between gap-3 border-surface-a20 border-t p-4 px-6">
        <div className="text-text-a30 text-xs leading-[1.4]">
          Format, Rating, and Language use AND conditions; others use OR.
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            className="cursor-pointer rounded-lg border border-surface-a20 bg-transparent px-6 py-2.5 font-medium text-sm text-text-a30 transition-[background-color_0.2s,color_0.2s,border-color_0.2s] hover:border-surface-a30 hover:bg-surface-tonal-a20 hover:text-text-a0 active:bg-surface-tonal-a30"
            onClick={handleClear}
          >
            Clear Filters
          </button>
          <button
            type="button"
            className="cursor-pointer rounded-lg border-none bg-primary-a0 px-6 py-2.5 font-medium text-sm text-text-a0 transition-[opacity_0.2s] hover:opacity-90 active:opacity-80"
            onClick={handleApply}
          >
            Apply Filter
          </button>
        </div>
      </div>
    </div>
  );
}
