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

import { z } from "zod";

/**
 * Zod schema for validating BookUpdate objects.
 *
 * Provides runtime validation and type inference for book update forms.
 * Follows DRY by centralizing validation logic.
 */

const identifierSchema = z.object({
  type: z.string().min(1, "Identifier type is required"),
  val: z.string().min(1, "Identifier value is required"),
});

/**
 * Zod schema for BookUpdate validation.
 *
 * Validates all fields that can be updated in a book edit form.
 * Most fields are optional to allow partial updates.
 */
export const bookUpdateSchema = z.object({
  title: z
    .string()
    .min(1, "Title is required")
    .max(1000, "Title must be less than 1000 characters")
    .optional(),
  pubdate: z
    .string()
    .refine(
      (val) =>
        val === "" ||
        /^\d{4}-\d{2}-\d{2}$/.test(val) ||
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(val),
      "Date must be in YYYY-MM-DD or ISO format",
    )
    .transform((val) => (val === "" ? null : val))
    .nullable()
    .optional(),
  author_names: z
    .array(z.string().min(1, "Author name cannot be empty"))
    .transform((val) => (val.length === 0 ? null : val))
    .nullable()
    .optional(),
  series_name: z
    .string()
    .max(400, "Series name must be less than 400 characters")
    .transform((val) => (val === "" ? null : val))
    .nullable()
    .optional(),
  series_id: z.number().int().positive().nullable().optional(),
  series_index: z
    .number()
    .min(0, "Series index must be 0 or greater")
    .max(10000, "Series index must be less than 10000")
    .nullable()
    .optional(),
  tag_names: z
    .array(z.string().min(1, "Tag cannot be empty"))
    .max(200, "Maximum 200 tags allowed")
    .transform((val) => (val.length === 0 ? null : val))
    .nullable()
    .optional(),
  identifiers: z
    .array(identifierSchema)
    .max(100, "Maximum 100 identifiers allowed")
    .transform((val) => (val.length === 0 ? null : val))
    .nullable()
    .optional(),
  description: z
    .string()
    .max(1000000, "Description must be less than 1,000,000 characters")
    .transform((val) => (val === "" ? null : val))
    .nullable()
    .optional(),
  publisher_name: z
    .string()
    .max(255, "Publisher name must be less than 255 characters")
    .transform((val) => (val === "" ? null : val))
    .nullable()
    .optional(),
  publisher_id: z.number().int().positive().nullable().optional(),
  language_codes: z
    .array(
      z
        .string()
        .regex(
          /^[a-z]{2,3}$/,
          "Language code must be 2-3 lowercase letters (ISO 639-1 or ISO 639-2/3)",
        ),
    )
    .max(10, "Maximum 10 languages allowed")
    .transform((val) => (val.length === 0 ? null : val))
    .nullable()
    .optional(),
  language_ids: z
    .array(z.number().int().positive())
    .max(10, "Maximum 10 languages allowed")
    .nullable()
    .optional(),
  rating_value: z
    .number({
      message: "Rating must be a number",
    })
    .min(0, "Rating must be between 0 and 5")
    .max(5, "Rating must be between 0 and 5")
    .transform((val) => Math.round(val))
    .refine((val) => Number.isInteger(val), {
      message: "Rating must be an integer",
    })
    .nullable()
    .optional(),
  rating_id: z.number().int().positive().nullable().optional(),
});

/**
 * Type inferred from the schema (matches BookUpdate).
 */
export type BookUpdateFormData = z.infer<typeof bookUpdateSchema>;
