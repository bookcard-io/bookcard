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

/**
 * Library list item component.
 *
 * Renders a single library item with checkbox, info, stats, and actions.
 * Follows SRP by focusing solely on individual library item rendering.
 */

"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/forms/Button";
import {
  CONVERSION_TARGET_FORMAT_OPTIONS,
  SUPPORTED_BOOK_FORMATS,
} from "@/components/profile/config/configurationConstants";
import { EditableTextField } from "@/components/profile/EditableNameField";
import { cn } from "@/libs/utils";
import type { LibraryStats } from "@/services/libraryStatsService";
import { LibraryStatsPills } from "./LibraryStatsPills";
import type { Library } from "./types";

export interface LibraryListItemProps {
  /** Library data. */
  library: Library;
  /** Library statistics (optional). */
  stats: LibraryStats | null | undefined;
  /** Whether stats are loading. */
  isLoadingStats: boolean | undefined;
  /** Callback when library is deleted. */
  onDelete: (id: number) => void;
  /** ID of library currently being deleted. */
  deletingLibraryId: number | null;
  /** Callback when library scan is initiated. */
  onScan: (libraryId: number) => void;
  /** ID of library currently being scanned. */
  scanningLibraryId: number | null;
  /** ID of library currently being updated. */
  updatingLibraryId: number | null;
  /** Callback when library is updated. */
  onUpdate: (
    libraryId: number,
    updates: {
      name?: string;
      auto_convert_on_ingest?: boolean;
      auto_metadata_enforcement?: boolean;
      auto_convert_target_format?: string | null;
      auto_convert_ignored_formats?: string | null;
      auto_convert_backup_originals?: boolean;
      epub_fixer_auto_fix_on_ingest?: boolean;
      duplicate_handling?: string;
    },
  ) => Promise<void>;
  /** Whether there is an active scan task for this library. */
  hasActiveScan: boolean;
}

/**
 * Library list item component.
 *
 * Renders a single library with its information, stats, and actions.
 *
 * Parameters
 * ----------
 * props : LibraryListItemProps
 *     Component props including library data and callbacks.
 */
export function LibraryListItem({
  library,
  stats,
  isLoadingStats,
  onDelete,
  deletingLibraryId,
  onScan,
  scanningLibraryId,
  onUpdate,
  hasActiveScan,
}: LibraryListItemProps) {
  const isScanning = scanningLibraryId === library.id || hasActiveScan;
  const [isExpanded, setIsExpanded] = useState(false);

  // Auto-convert settings state
  const [autoConvertOnIngest, setAutoConvertOnIngest] = useState(
    library.auto_convert_on_ingest ?? false,
  );
  const [targetFormat, setTargetFormat] = useState(
    library.auto_convert_target_format ?? "epub",
  );
  const [ignoredFormats, setIgnoredFormats] = useState<Set<string>>(new Set());
  const [backupOriginals, setBackupOriginals] = useState(
    library.auto_convert_backup_originals ?? true,
  );
  const [epubFixerAutoFix, setEpubFixerAutoFix] = useState(
    library.epub_fixer_auto_fix_on_ingest ?? false,
  );
  const [autoMetadataEnforcement, setAutoMetadataEnforcement] = useState(
    library.auto_metadata_enforcement ?? true,
  );
  const [duplicateHandling, setDuplicateHandling] = useState(
    library.duplicate_handling ?? "IGNORE",
  );

  // Track which specific field is updating to avoid disabling unrelated fields
  const [busyField, setBusyField] = useState<string | null>(null);

  // Load ignored formats from library
  useEffect(() => {
    if (library.auto_convert_ignored_formats) {
      try {
        const parsed = JSON.parse(
          library.auto_convert_ignored_formats,
        ) as string[];
        if (Array.isArray(parsed)) {
          setIgnoredFormats(new Set(parsed.map((f) => f.trim().toLowerCase())));
        }
      } catch {
        // Not JSON, try comma-separated string
        const formats = library.auto_convert_ignored_formats
          .split(",")
          .map((f) => f.trim().toLowerCase())
          .filter((f) => f.length > 0);
        setIgnoredFormats(new Set(formats));
      }
    }
  }, [library.auto_convert_ignored_formats]);

  // Sync state when library changes
  useEffect(() => {
    setAutoConvertOnIngest(library.auto_convert_on_ingest ?? false);
    setTargetFormat(library.auto_convert_target_format ?? "epub");
    setBackupOriginals(library.auto_convert_backup_originals ?? true);
    setEpubFixerAutoFix(library.epub_fixer_auto_fix_on_ingest ?? false);
    setAutoMetadataEnforcement(library.auto_metadata_enforcement ?? true);
    setDuplicateHandling(library.duplicate_handling ?? "IGNORE");
  }, [library]);

  const handleNameSave = async (name: string) => {
    await onUpdate(library.id, { name: name.trim() || library.name });
  };

  const handleAutoConvertToggle = async (value: boolean) => {
    setBusyField("auto_convert_on_ingest");
    setAutoConvertOnIngest(value);
    try {
      await onUpdate(library.id, { auto_convert_on_ingest: value });
    } finally {
      setBusyField(null);
    }
  };

  const handleTargetFormatChange = async (value: string) => {
    setBusyField("target_format");
    setTargetFormat(value);
    try {
      await onUpdate(library.id, { auto_convert_target_format: value });
    } finally {
      setBusyField(null);
    }
  };

  const handleFormatToggle = async (format: string) => {
    setBusyField("ignored_formats");
    const formatLower = format.toLowerCase();
    const next = new Set(ignoredFormats);
    if (next.has(formatLower)) {
      next.delete(formatLower);
    } else {
      next.add(formatLower);
    }
    setIgnoredFormats(next);

    // Save as JSON array
    const formatsArray = Array.from(next).sort();
    const jsonValue = JSON.stringify(formatsArray);
    try {
      await onUpdate(library.id, { auto_convert_ignored_formats: jsonValue });
    } finally {
      setBusyField(null);
    }
  };

  const handleBackupOriginalsToggle = async (value: boolean) => {
    setBusyField("backup_originals");
    setBackupOriginals(value);
    try {
      await onUpdate(library.id, { auto_convert_backup_originals: value });
    } finally {
      setBusyField(null);
    }
  };

  const handleEpubFixerToggle = async (value: boolean) => {
    setBusyField("epub_fixer");
    setEpubFixerAutoFix(value);
    try {
      await onUpdate(library.id, { epub_fixer_auto_fix_on_ingest: value });
    } finally {
      setBusyField(null);
    }
  };

  const handleAutoMetadataEnforcementToggle = async (value: boolean) => {
    setBusyField("auto_metadata_enforcement");
    setAutoMetadataEnforcement(value);
    try {
      await onUpdate(library.id, { auto_metadata_enforcement: value });
    } finally {
      setBusyField(null);
    }
  };

  const handleDuplicateHandlingChange = async (value: string) => {
    setBusyField("duplicate_handling");
    setDuplicateHandling(value);
    try {
      await onUpdate(library.id, { duplicate_handling: value });
    } finally {
      setBusyField(null);
    }
  };

  return (
    <div className="flex flex-col gap-3 rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-a10)] p-3">
      <div className="flex items-center gap-3">
        <div className="flex min-w-[250px] flex-1 items-center gap-3">
          <button
            type="button"
            onClick={() => setIsExpanded((prev) => !prev)}
            className="flex h-[18px] w-[18px] items-center justify-center text-[var(--color-text-a20)] transition-transform hover:text-[var(--color-text-a0)]"
            aria-label={isExpanded ? "Collapse settings" : "Expand settings"}
          >
            <i
              className={cn(
                "pi pi-chevron-right text-xs transition-transform",
                isExpanded && "rotate-90",
              )}
              aria-hidden="true"
            />
          </button>
          <div className="flex flex-1 flex-col gap-1">
            <div className="font-medium text-sm">
              <EditableTextField
                currentValue={library.name}
                onSave={handleNameSave}
                placeholder="Enter library name"
                editLabel="Edit library name"
                allowEmpty={false}
              />
            </div>
            <div className="break-all text-[var(--color-text-a30)] text-xs">
              {library.calibre_db_path}
            </div>
            {library.updated_at && (
              <div className="text-[11px] text-[var(--color-text-a40)]">
                Last updated: {new Date(library.updated_at).toLocaleString()}
              </div>
            )}
          </div>
        </div>
        {stats && <LibraryStatsPills stats={stats} />}
        {isLoadingStats === true && (
          <div className="text-[var(--color-text-a30)] text-xs">
            Loading stats...
          </div>
        )}
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="success"
            size="small"
            onClick={() => onScan(library.id)}
            disabled={isScanning || deletingLibraryId === library.id}
            loading={isScanning}
          >
            {hasActiveScan ? (
              <i className="pi pi-spinner animate-spin" aria-hidden="true" />
            ) : (
              <i className="pi pi-sync" aria-hidden="true" />
            )}
            Scan
          </Button>
          <Button
            type="button"
            variant="danger"
            size="small"
            onClick={() => onDelete(library.id)}
            disabled={deletingLibraryId === library.id || isScanning}
            className="bg-[var(--color-danger-a-1)] text-[var(--color-white)] hover:bg-[var(--color-danger-a0)]"
          >
            <i className="pi pi-trash" aria-hidden="true" />
            Remove
          </Button>
        </div>
      </div>

      {/* Settings - collapsible section */}
      {isExpanded && (
        <div className="border-[var(--color-surface-a20)] border-t pt-3">
          {/* Duplicate Handling */}
          <div className="mb-4 flex flex-col gap-2">
            <div className="font-semibold text-[var(--color-text-a0)] text-lg">
              Duplicate Handling
            </div>
            <div className="mb-1 text-[var(--color-text-a10)] text-xs">
              Strategy for handling duplicate books during ingest and upload
            </div>
            <div className="flex flex-wrap gap-4">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  name={`duplicate-handling-${library.id}`}
                  value="IGNORE"
                  checked={duplicateHandling === "IGNORE"}
                  onChange={(e) =>
                    handleDuplicateHandlingChange(e.target.value)
                  }
                  disabled={busyField === "duplicate_handling"}
                  className="h-4 w-4 cursor-pointer accent-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                />
                <span
                  className={cn(
                    "text-[var(--color-text-a0)] text-sm",
                    busyField === "duplicate_handling" && "opacity-50",
                  )}
                >
                  Ignore (skip duplicates, keep existing)
                </span>
              </label>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  name={`duplicate-handling-${library.id}`}
                  value="OVERWRITE"
                  checked={duplicateHandling === "OVERWRITE"}
                  onChange={(e) =>
                    handleDuplicateHandlingChange(e.target.value)
                  }
                  disabled={busyField === "duplicate_handling"}
                  className="h-4 w-4 cursor-pointer accent-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                />
                <span
                  className={cn(
                    "text-[var(--color-text-a0)] text-sm",
                    busyField === "duplicate_handling" && "opacity-50",
                  )}
                >
                  Overwrite (replace existing with incoming)
                </span>
              </label>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  name={`duplicate-handling-${library.id}`}
                  value="CREATE_NEW"
                  checked={duplicateHandling === "CREATE_NEW"}
                  onChange={(e) =>
                    handleDuplicateHandlingChange(e.target.value)
                  }
                  disabled={busyField === "duplicate_handling"}
                  className="h-4 w-4 cursor-pointer accent-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                />
                <span
                  className={cn(
                    "text-[var(--color-text-a0)] text-sm",
                    busyField === "duplicate_handling" && "opacity-50",
                  )}
                >
                  Create new (add even if duplicate)
                </span>
              </label>
            </div>
          </div>

          <div className="mb-3 font-semibold text-[var(--color-text-a0)] text-lg">
            Auto-Convert on Ingest Settings
          </div>
          <div className="flex flex-col gap-4">
            {/* Three-column layout for main toggles */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {/* Auto-convert on ingest toggle */}
              <div className="flex flex-col gap-2">
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={autoConvertOnIngest}
                    onChange={(e) => handleAutoConvertToggle(e.target.checked)}
                    disabled={busyField === "auto_convert_on_ingest"}
                    className="h-4 w-4 cursor-pointer rounded border-[var(--color-surface-a20)] text-[var(--color-primary-a0)] accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                  />
                  <span
                    className={cn(
                      "text-[var(--color-text-a0)] text-sm",
                      busyField === "auto_convert_on_ingest" && "opacity-50",
                    )}
                  >
                    Automatically convert books to target format during
                    auto-ingest
                  </span>
                </label>
              </div>

              {/* Auto metadata enforcement */}
              <div className="flex flex-col gap-2">
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={autoMetadataEnforcement}
                    onChange={(e) =>
                      handleAutoMetadataEnforcementToggle(e.target.checked)
                    }
                    disabled={busyField === "auto_metadata_enforcement"}
                    className="h-4 w-4 cursor-pointer rounded border-[var(--color-surface-a20)] text-[var(--color-primary-a0)] accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                  />
                  <span
                    className={cn(
                      "text-[var(--color-text-a0)] text-sm",
                      busyField === "auto_metadata_enforcement" && "opacity-50",
                    )}
                  >
                    Automatically enforce metadata and covers in ebook files
                  </span>
                </label>
              </div>

              {/* EPUB Fixer auto-fix on ingest */}
              <div className="flex flex-col gap-2">
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={epubFixerAutoFix}
                    onChange={(e) => handleEpubFixerToggle(e.target.checked)}
                    disabled={busyField === "epub_fixer"}
                    className="h-4 w-4 cursor-pointer rounded border-[var(--color-surface-a20)] text-[var(--color-primary-a0)] accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                  />
                  <span
                    className={cn(
                      "text-[var(--color-text-a0)] text-sm",
                      busyField === "epub_fixer" && "opacity-50",
                    )}
                  >
                    Automatically fix EPUB files on upload/ingest
                  </span>
                </label>
              </div>
            </div>

            {/* Target format */}
            {autoConvertOnIngest && (
              <>
                <div className="flex flex-col gap-2">
                  <div className="font-medium text-[var(--color-text-a20)] text-xs">
                    Target Format
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {CONVERSION_TARGET_FORMAT_OPTIONS.map((option) => (
                      <label
                        key={option.value}
                        className="flex cursor-pointer items-center gap-2"
                      >
                        <input
                          type="radio"
                          name={`target-format-${library.id}`}
                          value={option.value}
                          checked={targetFormat === option.value}
                          onChange={(e) =>
                            handleTargetFormatChange(e.target.value)
                          }
                          disabled={busyField === "target_format"}
                          className="h-4 w-4 cursor-pointer accent-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                        />
                        <span
                          className={cn(
                            "text-[var(--color-text-a0)] text-sm",
                            busyField === "target_format" && "opacity-50",
                          )}
                        >
                          {option.label}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Ignored formats */}
                <div className="flex flex-col gap-2">
                  <div className="font-medium text-[var(--color-text-a20)] text-xs">
                    Ignored Formats
                  </div>
                  <div className="mb-1 text-[var(--color-text-a30)] text-xs">
                    Select formats to skip during auto-conversion
                  </div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
                    {SUPPORTED_BOOK_FORMATS.map((format) => {
                      const isChecked = ignoredFormats.has(format.value);
                      return (
                        <label
                          key={format.value}
                          className="flex cursor-pointer items-center gap-2"
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => handleFormatToggle(format.value)}
                            disabled={busyField === "ignored_formats"}
                            className="h-4 w-4 shrink-0 cursor-pointer rounded border-[var(--color-surface-a20)] text-[var(--color-primary-a0)] accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                          />
                          <span
                            className={cn(
                              "text-[var(--color-text-a0)] text-sm",
                              busyField === "ignored_formats" && "opacity-50",
                            )}
                          >
                            {format.label}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                </div>

                {/* Backup originals */}
                <div className="flex flex-col gap-2">
                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="checkbox"
                      checked={backupOriginals}
                      onChange={(e) =>
                        handleBackupOriginalsToggle(e.target.checked)
                      }
                      disabled={busyField === "backup_originals"}
                      className="h-4 w-4 cursor-pointer rounded border-[var(--color-surface-a20)] text-[var(--color-primary-a0)] accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                    />
                    <span
                      className={cn(
                        "text-[var(--color-text-a0)] text-sm",
                        busyField === "backup_originals" && "opacity-50",
                      )}
                    >
                      Create backup copies of original files before conversion
                    </span>
                  </label>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
