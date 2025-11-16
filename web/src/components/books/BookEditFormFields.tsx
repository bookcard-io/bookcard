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

import { AutocompleteTextInput } from "@/components/forms/AutocompleteTextInput";
import { Button } from "@/components/forms/Button";
import { DateInput } from "@/components/forms/DateInput";
import { IdentifierInput } from "@/components/forms/IdentifierInput";
import { MultiTextInput } from "@/components/forms/MultiTextInput";
import { NumberInput } from "@/components/forms/NumberInput";
import { RatingInput } from "@/components/forms/RatingInput";
import { TagInput } from "@/components/forms/TagInput";
import { TextArea } from "@/components/forms/TextArea";
import { TextInput } from "@/components/forms/TextInput";
import { languageFilterSuggestionsService } from "@/services/filterSuggestionsService";
import type { Book, BookUpdate } from "@/types/book";

export interface BookEditFormFieldsProps {
  /** Current book being edited. */
  book: Book;
  /** Current form data. */
  formData: BookUpdate;
  /** Handler for field changes. */
  onFieldChange: <K extends keyof BookUpdate>(
    field: K,
    value: BookUpdate[K],
  ) => void;
}

/**
 * Form fields component for book edit modal.
 *
 * Displays all editable form fields in a grid layout.
 * Follows SRP by focusing solely on form field presentation.
 */
export function BookEditFormFields({
  book,
  formData,
  onFieldChange,
}: BookEditFormFieldsProps) {
  return (
    <div className="flex min-w-0 flex-col gap-6">
      <div className="grid grid-cols-3 gap-4 sm:grid-cols-1">
        {/* Row 1: Title and Title Sort */}
        <div className="col-span-full grid grid-cols-1 items-start gap-4 sm:grid-cols-[1fr_1fr]">
          <div className="grid min-w-0 grid-cols-[1fr_auto] items-end gap-3">
            <TextInput
              id="title"
              label="Title"
              value={formData.title || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                onFieldChange("title", e.target.value)
              }
              required
              className="min-w-0"
            />
            <button
              type="button"
              className="mb-2 flex items-center justify-center self-end border-none bg-transparent p-2 text-text-a30 text-xl transition-[transform,color] duration-200 hover:translate-x-0.5 hover:text-primary-a0 focus:rounded focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
              aria-label="Copy to title sort"
              title="Copy to title sort"
            >
              →
            </button>
          </div>
          <TextInput
            id="title_sort"
            label="Title Sort"
            value={book.title || ""}
            disabled
            className="min-w-0"
          />
        </div>

        {/* Row 2: Author(s) and Author(s) Sort */}
        <div className="col-span-full grid grid-cols-1 items-start gap-4 sm:grid-cols-[1fr_1fr]">
          <div className="grid min-w-0 grid-cols-[1fr_auto] items-end gap-3">
            <MultiTextInput
              id="authors"
              label="Author(s)"
              values={formData.author_names || []}
              onChange={(authors) => onFieldChange("author_names", authors)}
              placeholder="Add author names (press Enter or comma)"
              filterType="author"
            />
            <button
              type="button"
              className="mb-2 flex items-center justify-center self-end border-none bg-transparent p-2 text-text-a30 text-xl transition-[transform,color] duration-200 hover:translate-x-0.5 hover:text-primary-a0 focus:rounded focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
              aria-label="Copy to author sort"
              title="Copy to author sort"
            >
              →
            </button>
          </div>
          <TextInput
            id="author_sort"
            label="Author(s)"
            value={book.author_sort || ""}
            disabled
            className="min-w-0"
          />
        </div>

        {/* Row 3: Series, Number, Rating */}
        <div className="col-span-full grid grid-cols-1 items-end gap-4 sm:grid-cols-[2fr_1fr_1fr]">
          <AutocompleteTextInput
            id="series_name"
            label="Series"
            value={formData.series_name || ""}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              onFieldChange(
                "series_name",
                (e.target as HTMLInputElement).value || null,
              )
            }
            placeholder="Enter series name"
            filterType="series"
            className="min-w-0"
          />
          <NumberInput
            id="series_index"
            label="Number"
            value={formData.series_index ?? ""}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              onFieldChange(
                "series_index",
                e.target.value ? parseFloat(e.target.value) : null,
              )
            }
            step={0.1}
            min={0}
            className="min-w-0"
          />
          <div className="flex min-w-0 flex-col">
            <RatingInput
              id="rating"
              label="Rating"
              value={formData.rating_value ?? null}
              onChange={(rating) => onFieldChange("rating_value", rating)}
            />
          </div>
        </div>

        {/* Row 4: Tags and Manage Tags button */}
        <div className="col-span-full grid grid-cols-1 items-start gap-4 sm:grid-cols-[1fr_1fr]">
          <TagInput
            id="tags"
            label="Tags"
            tags={formData.tag_names || []}
            onChange={(tags) => onFieldChange("tag_names", tags)}
            placeholder="Add tags (press Enter or comma)"
            filterType="genre"
          />
          <div className="flex w-full flex-col gap-2">
            <div className="h-[1.3125rem] font-medium text-sm text-text-a10 leading-6">
              &nbsp;
            </div>
            <Button
              type="button"
              variant="primary"
              size="medium"
              className="h-11 self-start"
              onClick={() => {
                // TODO: Implement manage tags
              }}
            >
              Manage tags
            </Button>
          </div>
        </div>

        {/* Row 5: Identifiers and Languages */}
        <div className="col-span-full grid grid-cols-1 items-start gap-4 sm:grid-cols-[1fr_1fr]">
          <IdentifierInput
            id="identifiers"
            label="Identifiers"
            identifiers={formData.identifiers || []}
            onChange={(identifiers) =>
              onFieldChange("identifiers", identifiers)
            }
          />
          <TagInput
            id="languages"
            label="Languages (ISO 639-1 language code)"
            tags={formData.language_codes || []}
            onChange={(languages) =>
              onFieldChange(
                "language_codes",
                languages.length > 0 ? languages : null,
              )
            }
            placeholder="Add language code"
            filterType="language"
            suggestionsService={languageFilterSuggestionsService}
          />
        </div>

        {/* Row 6: Publisher and Publish date */}
        <div className="col-span-full grid grid-cols-1 items-start gap-4 sm:grid-cols-[1fr_1fr]">
          <AutocompleteTextInput
            id="publisher"
            label="Publisher"
            value={formData.publisher_name || ""}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              onFieldChange(
                "publisher_name",
                (e.target as HTMLInputElement).value || null,
              )
            }
            placeholder="Enter publisher name"
            filterType="publisher"
          />
          <DateInput
            id="pubdate"
            label="Publish date"
            value={formData.pubdate || ""}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              onFieldChange("pubdate", e.target.value || null)
            }
          />
        </div>
      </div>

      {/* Full-width Description */}
      <div className="mt-2 flex flex-col gap-3">
        <TextArea
          id="description"
          label="Description"
          value={formData.description || ""}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
            onFieldChange("description", e.target.value || null)
          }
          placeholder="Enter book description..."
          rows={6}
        />
      </div>
    </div>
  );
}
