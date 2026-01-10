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
import { MonitorMode } from "@/types/trackedBook";

/**
 * Zod schema for validating tracked book updates.
 *
 * Mirrors the validation approach used by `bookUpdateSchema` but targets
 * the tracked-book model (PVR).
 */
const trackedBookStatusSchema = z.enum([
  "wanted",
  "searching",
  "downloading",
  "paused",
  "stalled",
  "seeding",
  "completed",
  "failed",
  "ignored",
]);

const monitorModeSchema = z.nativeEnum(MonitorMode);

export const trackedBookUpdateSchema = z
  .object({
    title: z
      .string()
      .min(1, "Title is required")
      .max(500, "Title must be less than 500 characters"),
    author: z
      .string()
      .min(1, "Author is required")
      .max(500, "Author must be less than 500 characters"),
    isbn: z
      .string()
      .max(20, "ISBN must be less than 20 characters")
      .transform((val) => (val === "" ? null : val))
      .nullable()
      .optional(),
    cover_url: z
      .string()
      .refine(
        (val) =>
          val === "" ||
          val.startsWith("/") ||
          val.startsWith("http://") ||
          val.startsWith("https://"),
        "Cover URL must be an absolute URL or a /path",
      )
      .max(2000, "Cover URL must be less than 2000 characters")
      .transform((val) => (val === "" ? null : val))
      .nullable()
      .optional(),
    description: z
      .string()
      .max(1000000, "Description must be less than 1,000,000 characters")
      .transform((val) => (val === "" ? null : val))
      .nullable()
      .optional(),
    publisher: z
      .string()
      .max(500, "Publisher must be less than 500 characters")
      .transform((val) => (val === "" ? null : val))
      .nullable()
      .optional(),
    published_date: z
      .string()
      .max(50, "Published date must be less than 50 characters")
      .refine(
        (val) =>
          val === "" ||
          /^\d{4}$/.test(val) ||
          /^\d{4}-\d{2}-\d{2}$/.test(val) ||
          /^\d{4}-\d{2}$/.test(val),
        "Published date must be YYYY, YYYY-MM, or YYYY-MM-DD",
      )
      .transform((val) => (val === "" ? null : val))
      .nullable()
      .optional(),
    rating: z
      .number({
        message: "Rating must be a number",
      })
      .min(0, "Rating must be 0 or greater")
      .max(100, "Rating must be 100 or less")
      .nullable()
      .optional(),
    tags: z
      .array(z.string().min(1, "Tag cannot be empty"))
      .max(200, "Maximum 200 tags allowed")
      .transform((val) => (val.length === 0 ? null : val))
      .nullable()
      .optional(),
    series_name: z
      .string()
      .max(500, "Series name must be less than 500 characters")
      .transform((val) => (val === "" ? null : val))
      .nullable()
      .optional(),
    series_index: z
      .number()
      .min(0, "Series index must be 0 or greater")
      .max(10000, "Series index must be less than 10000")
      .nullable()
      .optional(),
    status: trackedBookStatusSchema.optional(),
    monitor_mode: monitorModeSchema.optional(),
    auto_search_enabled: z.boolean().optional(),
    auto_download_enabled: z.boolean().optional(),
    preferred_formats: z
      .array(z.string().min(1, "Format cannot be empty"))
      .max(50, "Maximum 50 preferred formats allowed")
      .transform((val) => (val.length === 0 ? null : val))
      .nullable()
      .optional(),
    exclude_keywords: z
      .array(z.string().min(1, "Keyword cannot be empty"))
      .max(200, "Maximum 200 exclude keywords allowed")
      .transform((val) => (val.length === 0 ? null : val))
      .nullable()
      .optional(),
    require_keywords: z
      .array(z.string().min(1, "Keyword cannot be empty"))
      .max(200, "Maximum 200 required keywords allowed")
      .transform((val) => (val.length === 0 ? null : val))
      .nullable()
      .optional(),
    require_title_match: z.boolean().optional(),
    require_author_match: z.boolean().optional(),
    require_isbn_match: z.boolean().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.require_isbn_match && !data.isbn) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["isbn"],
        message: "ISBN is required when 'Require ISBN match' is enabled",
      });
    }
  });

export type TrackedBookUpdateFormData = z.infer<typeof trackedBookUpdateSchema>;
