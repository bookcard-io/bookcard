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

import { Controller, type UseFormReturn } from "react-hook-form";
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
import { useUser } from "@/contexts/UserContext";
import type { BookUpdateFormData } from "@/schemas/bookUpdateSchema";
import { languageFilterSuggestionsService } from "@/services/filterSuggestionsService";
import type { Book } from "@/types/book";
import { buildBookPermissionContext } from "@/utils/permissions";

export interface BookEditFormFieldsProps {
  /** Current book being edited. */
  book: Book;
  /** React Hook Form instance. */
  form: UseFormReturn<BookUpdateFormData>;
}

/**
 * Form fields component for book edit modal.
 *
 * Displays all editable form fields in a grid layout.
 * Follows SRP by focusing solely on form field presentation.
 */
export function BookEditFormFields({ book, form }: BookEditFormFieldsProps) {
  const { canPerformAction } = useUser();
  const bookContext = buildBookPermissionContext(book);
  const canWrite = canPerformAction("books", "write", bookContext);

  const {
    control,
    formState: { errors },
  } = form;

  return (
    <div className="flex min-w-0 flex-col gap-6">
      <div className="grid grid-cols-3 gap-4 sm:grid-cols-1">
        {/* Row 1: Title and Title Sort */}
        <div className="col-span-full grid grid-cols-1 items-start gap-4 sm:grid-cols-[1fr_1fr]">
          <div className="grid min-w-0 grid-cols-[1fr_auto] items-end gap-3">
            <Controller
              name="title"
              control={control}
              rules={{ required: "Title is required" }}
              render={({ field }) => (
                <TextInput
                  id="title"
                  label="Title"
                  {...field}
                  value={field.value || ""}
                  error={errors.title?.message}
                  disabled={!canWrite}
                  className="min-w-0"
                />
              )}
            />
            <button
              type="button"
              disabled={!canWrite}
              className="mb-2 flex items-center justify-center self-end border-none bg-transparent p-2 text-text-a30 text-xl transition-[transform,color] duration-200 hover:translate-x-0.5 hover:text-primary-a0 focus:rounded focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Copy to title sort"
              title="Copy to title sort"
            >
              →
            </button>
          </div>
          <TextInput
            id="title_sort"
            label="Title Sort"
            value={book.title_sort || ""}
            disabled
            className="min-w-0"
          />
        </div>

        {/* Row 2: Author(s) and Author(s) Sort */}
        <div className="col-span-full grid grid-cols-1 items-start gap-4 sm:grid-cols-[1fr_1fr]">
          <div className="grid min-w-0 grid-cols-[1fr_auto] items-end gap-3">
            <Controller
              name="author_names"
              control={control}
              rules={{ required: "At least one author is required" }}
              render={({ field }) => (
                <MultiTextInput
                  id="authors"
                  label="Author(s)"
                  values={field.value || []}
                  onChange={field.onChange}
                  placeholder="Add author names (press Enter or comma)"
                  filterType="author"
                  error={errors.author_names?.message}
                  disabled={!canWrite}
                />
              )}
            />
            <button
              type="button"
              disabled={!canWrite}
              className="mb-2 flex items-center justify-center self-end border-none bg-transparent p-2 text-text-a30 text-xl transition-[transform,color] duration-200 hover:translate-x-0.5 hover:text-primary-a0 focus:rounded focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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
          <Controller
            name="series_name"
            control={control}
            render={({ field }) => (
              <AutocompleteTextInput
                id="series_name"
                label="Series"
                value={field.value || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  const value = (e.target as HTMLInputElement).value || null;
                  field.onChange(value);
                }}
                placeholder="Enter series name"
                filterType="series"
                error={errors.series_name?.message}
                disabled={!canWrite}
                className="min-w-0"
              />
            )}
          />
          <Controller
            name="series_index"
            control={control}
            render={({ field }) => (
              <NumberInput
                id="series_index"
                label="Number"
                value={field.value ?? ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  const value = e.target.value
                    ? parseFloat(e.target.value)
                    : null;
                  field.onChange(value);
                }}
                step={0.1}
                min={0}
                error={errors.series_index?.message}
                disabled={!canWrite}
                className="min-w-0"
              />
            )}
          />
          <div className="flex min-w-0 flex-col">
            <Controller
              name="rating_value"
              control={control}
              render={({ field }) => (
                <RatingInput
                  id="rating"
                  label="Rating"
                  value={field.value ?? null}
                  onChange={field.onChange}
                  error={errors.rating_value?.message}
                  disabled={!canWrite}
                />
              )}
            />
          </div>
        </div>

        {/* Row 4: Tags and Manage Tags button */}
        <div className="col-span-full grid grid-cols-1 items-start gap-4 sm:grid-cols-[1fr_1fr]">
          <Controller
            name="tag_names"
            control={control}
            render={({ field }) => (
              <TagInput
                id="tags"
                label="Tags"
                tags={field.value || []}
                onChange={field.onChange}
                placeholder="Add tags (press Enter or comma)"
                filterType="genre"
                error={errors.tag_names?.message}
                disabled={!canWrite}
              />
            )}
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
              onClick={
                canWrite
                  ? () => {
                      // TODO: Implement manage tags
                    }
                  : undefined
              }
              disabled={!canWrite}
            >
              Manage tags
            </Button>
          </div>
        </div>

        {/* Row 5: Identifiers and Languages */}
        <div className="col-span-full grid grid-cols-1 items-start gap-4 sm:grid-cols-[1fr_1fr]">
          <Controller
            name="identifiers"
            control={control}
            render={({ field }) => (
              <IdentifierInput
                id="identifiers"
                label="Identifiers"
                identifiers={field.value || []}
                onChange={field.onChange}
                error={errors.identifiers?.message}
                disabled={!canWrite}
              />
            )}
          />
          <Controller
            name="language_codes"
            control={control}
            render={({ field }) => (
              <TagInput
                id="languages"
                label="Languages (ISO 639-1 language code)"
                tags={field.value || []}
                onChange={(languages) => {
                  const value = languages.length > 0 ? languages : null;
                  field.onChange(value);
                }}
                placeholder="Add language code"
                filterType="language"
                suggestionsService={languageFilterSuggestionsService}
                error={errors.language_codes?.message}
                disabled={!canWrite}
              />
            )}
          />
        </div>

        {/* Row 6: Publisher and Publish date */}
        <div className="col-span-full grid grid-cols-1 items-start gap-4 sm:grid-cols-[1fr_1fr]">
          <Controller
            name="publisher_name"
            control={control}
            render={({ field }) => (
              <AutocompleteTextInput
                id="publisher"
                label="Publisher"
                value={field.value || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  const value = (e.target as HTMLInputElement).value || null;
                  field.onChange(value);
                }}
                placeholder="Enter publisher name"
                filterType="publisher"
                error={errors.publisher_name?.message}
                disabled={!canWrite}
              />
            )}
          />
          <Controller
            name="pubdate"
            control={control}
            render={({ field }) => (
              <DateInput
                id="pubdate"
                label="Publish date"
                {...field}
                value={field.value || ""}
                error={errors.pubdate?.message}
                disabled={!canWrite}
              />
            )}
          />
        </div>
      </div>

      {/* Full-width Description */}
      <div className="mt-2 flex flex-col gap-3">
        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <TextArea
              id="description"
              label="Description"
              {...field}
              value={field.value || ""}
              error={errors.description?.message}
              placeholder="Enter book description..."
              rows={6}
              disabled={!canWrite}
            />
          )}
        />
      </div>
    </div>
  );
}
