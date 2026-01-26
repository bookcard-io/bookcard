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

import { COMMON_TARGET_FORMATS } from "@/constants/conversion";
import type { Book } from "@/types/book";

export function normalizeFormat(format: string): string {
  return format.trim().toUpperCase();
}

export function getAvailableFormats(book: Book): string[] {
  return book.formats?.map((f) => normalizeFormat(f.format)) ?? [];
}

export function getTargetFormatOptions(availableFormats: string[]): string[] {
  return COMMON_TARGET_FORMATS.filter(
    (format) => !availableFormats.includes(format),
  );
}

export function getConversionValidationError(
  sourceFormat: string,
  targetFormat: string,
): string | null {
  if (!sourceFormat || !targetFormat) {
    return "Please select both source and target formats";
  }
  if (sourceFormat === targetFormat) {
    return "Source and target formats must be different";
  }
  return null;
}
