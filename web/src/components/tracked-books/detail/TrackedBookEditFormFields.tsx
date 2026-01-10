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
import { MultiTextInput } from "@/components/forms/MultiTextInput";
import { NumberInput } from "@/components/forms/NumberInput";
import { Select } from "@/components/forms/Select";
import { TagInput } from "@/components/forms/TagInput";
import { TextArea } from "@/components/forms/TextArea";
import { TextInput } from "@/components/forms/TextInput";
import type { TrackedBookUpdateFormData } from "@/schemas/trackedBookUpdateSchema";
import { MonitorMode } from "@/types/trackedBook";

export interface TrackedBookEditFormFieldsProps {
  /** React Hook Form instance. */
  form: UseFormReturn<TrackedBookUpdateFormData>;
}

function parseAuthorPills(author: string | null | undefined): string[] {
  if (!author) return [];
  return author
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function joinAuthorPills(authors: string[]): string {
  return authors
    .map((s) => s.trim())
    .filter(Boolean)
    .join(", ");
}

/**
 * Form fields for the tracked book edit modal.
 *
 * Focuses on presentation only (SRP), with validation managed by schema + form.
 */
export function TrackedBookEditFormFields({
  form,
}: TrackedBookEditFormFieldsProps) {
  const {
    control,
    formState: { errors },
  } = form;

  return (
    <div className="flex min-w-0 flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Controller
          name="title"
          control={control}
          rules={{ required: "Title is required" }}
          render={({ field }) => (
            <TextInput
              id="tracked_title"
              label="Title"
              {...field}
              value={field.value || ""}
              error={errors.title?.message}
              className="min-w-0"
            />
          )}
        />

        <Controller
          name="author"
          control={control}
          rules={{ required: "Author is required" }}
          render={({ field }) => (
            <MultiTextInput
              id="tracked_author"
              label="Author"
              values={parseAuthorPills(field.value)}
              onChange={(values) => field.onChange(joinAuthorPills(values))}
              placeholder="Add author names (press Enter or comma)"
              filterType="author"
              error={errors.author?.message}
            />
          )}
        />

        <Controller
          name="series_name"
          control={control}
          render={({ field }) => (
            <AutocompleteTextInput
              id="tracked_series"
              label="Series"
              value={field.value || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                const value = (e.target as HTMLInputElement).value || null;
                field.onChange(value);
              }}
              placeholder="Enter series name"
              filterType="series"
              error={errors.series_name?.message}
              className="min-w-0"
            />
          )}
        />

        <Controller
          name="series_index"
          control={control}
          render={({ field }) => (
            <NumberInput
              id="tracked_series_index"
              label="Series #"
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
              className="min-w-0"
            />
          )}
        />

        <Controller
          name="publisher"
          control={control}
          render={({ field }) => (
            <AutocompleteTextInput
              id="tracked_publisher"
              label="Publisher"
              value={field.value || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                const value = (e.target as HTMLInputElement).value || null;
                field.onChange(value);
              }}
              placeholder="Enter publisher name"
              filterType="publisher"
              error={errors.publisher?.message}
              className="min-w-0"
            />
          )}
        />

        <Controller
          name="published_date"
          control={control}
          render={({ field }) => (
            <TextInput
              id="tracked_published_date"
              label="Published"
              {...field}
              value={field.value || ""}
              placeholder="YYYY, YYYY-MM, or YYYY-MM-DD"
              error={errors.published_date?.message}
              className="min-w-0"
            />
          )}
        />

        <Controller
          name="isbn"
          control={control}
          render={({ field }) => (
            <TextInput
              id="tracked_isbn"
              label="ISBN"
              {...field}
              value={field.value || ""}
              error={errors.isbn?.message}
              className="min-w-0"
            />
          )}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Controller
          name="status"
          control={control}
          render={({ field }) => (
            <Select
              id="tracked_status"
              label="Status"
              value={field.value || "wanted"}
              onChange={(e) => field.onChange(e.target.value)}
              error={errors.status?.message as string | undefined}
              options={[
                { value: "wanted", label: "Wanted" },
                { value: "searching", label: "Searching" },
                { value: "downloading", label: "Downloading" },
                { value: "paused", label: "Paused" },
                { value: "stalled", label: "Stalled" },
                { value: "seeding", label: "Seeding" },
                { value: "completed", label: "Completed" },
                { value: "failed", label: "Failed" },
                { value: "ignored", label: "Ignored" },
              ]}
            />
          )}
        />

        <Controller
          name="monitor_mode"
          control={control}
          render={({ field }) => (
            <Select
              id="tracked_monitor_mode"
              label="Monitor mode"
              value={field.value || MonitorMode.BOOK_ONLY}
              onChange={(e) => field.onChange(e.target.value as MonitorMode)}
              error={errors.monitor_mode?.message as string | undefined}
              options={[
                { value: MonitorMode.BOOK_ONLY, label: "Book only" },
                { value: MonitorMode.SERIES, label: "Series" },
                { value: MonitorMode.AUTHOR, label: "Author" },
              ]}
            />
          )}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Controller
          name="preferred_formats"
          control={control}
          render={({ field }) => (
            <MultiTextInput
              id="tracked_preferred_formats"
              label="Preferred formats"
              values={field.value || []}
              onChange={field.onChange}
              placeholder="Add formats (e.g., EPUB, PDF)"
              filterType="format"
              error={errors.preferred_formats?.message as string | undefined}
            />
          )}
        />

        <Controller
          name="tags"
          control={control}
          render={({ field }) => (
            <TagInput
              id="tracked_tags"
              label="Tags"
              tags={field.value || []}
              onChange={field.onChange}
              placeholder="Add tags (press Enter or comma)"
              filterType="genre"
              error={errors.tags?.message as string | undefined}
            />
          )}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Controller
          name="exclude_keywords"
          control={control}
          render={({ field }) => (
            <TagInput
              id="tracked_exclude_keywords"
              label="Exclude keywords"
              tags={field.value || []}
              onChange={field.onChange}
              placeholder="Add exclude keywords"
              error={errors.exclude_keywords?.message as string | undefined}
            />
          )}
        />

        <Controller
          name="require_keywords"
          control={control}
          render={({ field }) => (
            <TagInput
              id="tracked_require_keywords"
              label="Required keywords"
              tags={field.value || []}
              onChange={field.onChange}
              placeholder="Add required keywords"
              error={errors.require_keywords?.message as string | undefined}
            />
          )}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Controller
          name="require_title_match"
          control={control}
          render={({ field }) => (
            <Select
              id="tracked_require_title_match"
              label="Require title match"
              value={String(field.value ?? true)}
              onChange={(e) => field.onChange(e.target.value === "true")}
              options={[
                { value: "true", label: "Yes" },
                { value: "false", label: "No" },
              ]}
            />
          )}
        />
        <Controller
          name="require_author_match"
          control={control}
          render={({ field }) => (
            <Select
              id="tracked_require_author_match"
              label="Require author match"
              value={String(field.value ?? true)}
              onChange={(e) => field.onChange(e.target.value === "true")}
              options={[
                { value: "true", label: "Yes" },
                { value: "false", label: "No" },
              ]}
            />
          )}
        />
        <Controller
          name="require_isbn_match"
          control={control}
          render={({ field }) => (
            <Select
              id="tracked_require_isbn_match"
              label="Require ISBN match"
              value={String(field.value ?? false)}
              onChange={(e) => field.onChange(e.target.value === "true")}
              options={[
                { value: "false", label: "No" },
                { value: "true", label: "Yes" },
              ]}
              error={errors.require_isbn_match?.message as string | undefined}
            />
          )}
        />
      </div>

      <div className="mt-2 flex flex-col gap-3">
        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <TextArea
              id="tracked_description"
              label="Description"
              {...field}
              value={field.value || ""}
              error={errors.description?.message}
              placeholder="Enter description..."
              rows={6}
            />
          )}
        />
      </div>
    </div>
  );
}
