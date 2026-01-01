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

import { useEffect, useMemo, useState } from "react";
import { useLibraryManagement } from "@/components/admin/library/hooks/useLibraryManagement";
import {
  type FormatMode,
  formatModeService,
} from "@/services/FormatModeService";
import { type MetadataSearchResult, MonitorMode } from "@/types/trackedBook";

export interface AddBookFormState {
  libraryId: number | undefined;
  monitor: MonitorMode;
  monitorValue: string;
  preferredFormats: string[];
  tags: string[];
}

export function useAddBookForm(
  book: MetadataSearchResult | null,
  isOpen: boolean,
) {
  const { libraries } = useLibraryManagement();

  // Settings state
  const [libraryId, setLibraryId] = useState<number | undefined>(undefined);
  const [monitor, setMonitor] = useState<MonitorMode>(MonitorMode.BOOK_ONLY);
  const [monitorValue, setMonitorValue] = useState("");
  const [preferredFormats, setPreferredFormats] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);

  // Derived current format mode using the new detector
  const currentFormatMode = useMemo(() => {
    return formatModeService.detect(preferredFormats);
  }, [preferredFormats]);

  const handleFormatModeChange = (mode: string) => {
    const formats = formatModeService.getFormatsForMode(mode as FormatMode);
    setPreferredFormats([...formats]);
  };

  const handleMonitorChange = (mode: MonitorMode) => {
    setMonitor(mode);
    // Pre-fill monitor value based on mode if empty
    if (mode === MonitorMode.AUTHOR && book?.author) {
      setMonitorValue(book.author);
    } else {
      setMonitorValue("");
    }
  };

  // Reset state when book changes
  useEffect(() => {
    if (isOpen && book) {
      // Default to first library if available
      if (libraries.length > 0 && libraryId === undefined) {
        setLibraryId(libraries[0]?.id);
      } else if (libraries.length > 0 && libraryId !== undefined) {
        // Verify selected library still exists, if not fallback
        const exists = libraries.some((l) => l.id === libraryId);
        if (!exists) setLibraryId(libraries[0]?.id);
      }

      // Default settings
      setMonitor(MonitorMode.BOOK_ONLY);
      setMonitorValue("");
      setPreferredFormats([]);
      setTags(book.tags || []);
    }
  }, [isOpen, book, libraries, libraryId]);

  return {
    formState: {
      libraryId,
      monitor,
      monitorValue,
      preferredFormats,
      tags,
    },
    setLibraryId,
    setMonitor: handleMonitorChange,
    setMonitorValue,
    setPreferredFormats,
    setTags,
    currentFormatMode,
    handleFormatModeChange,
    libraries,
  };
}
