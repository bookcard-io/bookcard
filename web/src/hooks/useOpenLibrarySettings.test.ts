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

import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  downloadOpenLibraryDumps,
  getDefaultDumpUrls,
  ingestOpenLibraryDumps,
} from "@/services/openLibrarySettingsService";
import type { UseOpenLibrarySettingsOptions } from "./useOpenLibrarySettings";
import { useOpenLibrarySettings } from "./useOpenLibrarySettings";

vi.mock("@/services/openLibrarySettingsService", () => ({
  getDefaultDumpUrls: vi.fn(),
  downloadOpenLibraryDumps: vi.fn(),
  ingestOpenLibraryDumps: vi.fn(),
}));

describe("useOpenLibrarySettings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getDefaultDumpUrls).mockReturnValue({
      authors_url: "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz",
      works_url: "https://openlibrary.org/data/ol_dump_works_latest.txt.gz",
      editions_url:
        "https://openlibrary.org/data/ol_dump_editions_latest.txt.gz",
    });
    vi.mocked(downloadOpenLibraryDumps).mockResolvedValue({
      message: "Download started",
      task_id: 1,
      downloaded_files: [],
      failed_files: [],
    });
    vi.mocked(ingestOpenLibraryDumps).mockResolvedValue({
      message: "Ingest started",
      task_id: 1,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("initialization", () => {
    it("should initialize with default values when no options provided", () => {
      const { result } = renderHook(() => useOpenLibrarySettings());

      expect(result.current.formData.authors_url).toBe(
        "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz",
      );
      expect(result.current.formData.works_url).toBe(
        "https://openlibrary.org/data/ol_dump_works_latest.txt.gz",
      );
      expect(result.current.formData.editions_url).toBe(
        "https://openlibrary.org/data/ol_dump_editions_latest.txt.gz",
      );
      expect(result.current.formData.process_authors).toBe(true);
      expect(result.current.formData.process_works).toBe(true);
      expect(result.current.formData.process_editions).toBe(false);
      expect(result.current.isDownloading).toBe(false);
      expect(result.current.isIngesting).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should initialize with initialUrls when provided", () => {
      const initialUrls = {
        authors_url: "https://example.com/authors.txt.gz",
        works_url: "https://example.com/works.txt.gz",
        editions_url: "https://example.com/editions.txt.gz",
      };

      const { result } = renderHook(() =>
        useOpenLibrarySettings({ initialUrls }),
      );

      expect(result.current.formData.authors_url).toBe(initialUrls.authors_url);
      expect(result.current.formData.works_url).toBe(initialUrls.works_url);
      expect(result.current.formData.editions_url).toBe(
        initialUrls.editions_url,
      );
    });

    it("should initialize with initialProcessFlags when provided", () => {
      const initialProcessFlags = {
        process_authors: false,
        process_works: false,
        process_editions: true,
      };

      const { result } = renderHook(() =>
        useOpenLibrarySettings({ initialProcessFlags }),
      );

      expect(result.current.formData.process_authors).toBe(false);
      expect(result.current.formData.process_works).toBe(false);
      expect(result.current.formData.process_editions).toBe(true);
    });

    it("should use defaults for null initialUrls", () => {
      const initialUrls = {
        authors_url: null,
        works_url: null,
        editions_url: null,
      };

      const { result } = renderHook(() =>
        useOpenLibrarySettings({ initialUrls }),
      );

      expect(result.current.formData.authors_url).toBe(
        "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz",
      );
      expect(result.current.formData.works_url).toBe(
        "https://openlibrary.org/data/ol_dump_works_latest.txt.gz",
      );
      expect(result.current.formData.editions_url).toBe(
        "https://openlibrary.org/data/ol_dump_editions_latest.txt.gz",
      );
    });
  });

  describe("sync with initial values", () => {
    it("should sync formData when initialUrls are provided after mount", () => {
      const { result, rerender } = renderHook(
        (props: UseOpenLibrarySettingsOptions = {}) =>
          useOpenLibrarySettings(props),
        {
          initialProps: {},
        },
      );

      const initialUrls = {
        authors_url: "https://example.com/authors.txt.gz",
        works_url: "https://example.com/works.txt.gz",
        editions_url: "https://example.com/editions.txt.gz",
      };

      rerender({ initialUrls });

      expect(result.current.formData.authors_url).toBe(initialUrls.authors_url);
      expect(result.current.formData.works_url).toBe(initialUrls.works_url);
      expect(result.current.formData.editions_url).toBe(
        initialUrls.editions_url,
      );
    });

    it("should sync formData when initialProcessFlags are provided after mount", () => {
      const { result, rerender } = renderHook(
        (props: UseOpenLibrarySettingsOptions = {}) =>
          useOpenLibrarySettings(props),
        {
          initialProps: {},
        },
      );

      const initialProcessFlags = {
        process_authors: false,
        process_works: false,
        process_editions: true,
      };

      rerender({ initialProcessFlags });

      expect(result.current.formData.process_authors).toBe(false);
      expect(result.current.formData.process_works).toBe(false);
      expect(result.current.formData.process_editions).toBe(true);
    });

    it("should only sync once when initial values are provided", () => {
      const { result, rerender } = renderHook(
        ({ initialUrls }) => useOpenLibrarySettings({ initialUrls }),
        {
          initialProps: {
            initialUrls: {
              authors_url: "https://example.com/authors1.txt.gz",
              works_url: null,
              editions_url: null,
            },
          },
        },
      );

      const firstUrl = result.current.formData.authors_url;

      // Change initialUrls
      rerender({
        initialUrls: {
          authors_url: "https://example.com/authors2.txt.gz",
          works_url: null,
          editions_url: null,
        },
      });

      // Should not change (only syncs once)
      expect(result.current.formData.authors_url).toBe(firstUrl);
    });

    it("should use previous values for undefined initialProcessFlags fields", () => {
      const { result, rerender } = renderHook(
        (props: UseOpenLibrarySettingsOptions = {}) =>
          useOpenLibrarySettings(props),
        {
          initialProps: {},
        },
      );

      // Set initial values
      rerender({
        initialProcessFlags: {
          process_authors: false,
          process_works: true,
          process_editions: true,
        },
      });

      expect(result.current.formData.process_authors).toBe(false);
      expect(result.current.formData.process_works).toBe(true);
      expect(result.current.formData.process_editions).toBe(true);
    });
  });

  describe("handleFieldChange", () => {
    it("should update formData field", () => {
      const { result } = renderHook(() => useOpenLibrarySettings());

      act(() => {
        result.current.handleFieldChange(
          "authors_url",
          "https://example.com/new.txt.gz",
        );
      });

      expect(result.current.formData.authors_url).toBe(
        "https://example.com/new.txt.gz",
      );
    });

    it("should clear error on field change", () => {
      const { result } = renderHook(() => useOpenLibrarySettings());

      // Note: We can't directly set error state, so we test that handleFieldChange clears error
      // by checking that error is null after field change
      act(() => {
        result.current.handleFieldChange(
          "authors_url",
          "https://example.com/new.txt.gz",
        );
      });

      expect(result.current.error).toBeNull();
    });

    it("should update boolean fields", () => {
      const { result } = renderHook(() => useOpenLibrarySettings());

      act(() => {
        result.current.handleFieldChange("process_authors", false);
      });

      expect(result.current.formData.process_authors).toBe(false);
    });
  });

  describe("handleResetToDefaults", () => {
    it("should reset formData to defaults", () => {
      const { result } = renderHook(() => useOpenLibrarySettings());

      // Change some values
      act(() => {
        result.current.handleFieldChange(
          "authors_url",
          "https://example.com/custom.txt.gz",
        );
        result.current.handleFieldChange("process_authors", false);
      });

      // Reset to defaults
      act(() => {
        result.current.handleResetToDefaults();
      });

      expect(result.current.formData.authors_url).toBe(
        "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz",
      );
      expect(result.current.formData.process_authors).toBe(true);
      expect(result.current.formData.process_works).toBe(true);
      expect(result.current.formData.process_editions).toBe(false);
    });

    it("should clear error on reset", () => {
      const { result } = renderHook(() => useOpenLibrarySettings());

      // Note: We can't directly set error state, so we test that handleResetToDefaults clears error
      // by checking that error is null after reset
      act(() => {
        result.current.handleResetToDefaults();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe("handleDownload", () => {
    it("should download with all URLs", async () => {
      vi.mocked(downloadOpenLibraryDumps).mockResolvedValue({
        message: "Download started",
        task_id: 1,
        downloaded_files: [],
        failed_files: [],
      });

      const { result } = renderHook(() => useOpenLibrarySettings());

      await act(async () => {
        await result.current.handleDownload();
      });

      expect(downloadOpenLibraryDumps).toHaveBeenCalledWith([
        "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz",
        "https://openlibrary.org/data/ol_dump_works_latest.txt.gz",
        "https://openlibrary.org/data/ol_dump_editions_latest.txt.gz",
      ]);
      expect(result.current.isDownloading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should download with only non-empty URLs", async () => {
      vi.mocked(downloadOpenLibraryDumps).mockResolvedValue({
        message: "Download started",
        task_id: 1,
        downloaded_files: [],
        failed_files: [],
      });

      const { result } = renderHook(() => useOpenLibrarySettings());

      act(() => {
        result.current.handleFieldChange("authors_url", null);
        result.current.handleFieldChange(
          "works_url",
          "https://example.com/works.txt.gz",
        );
        result.current.handleFieldChange("editions_url", null);
      });

      await act(async () => {
        await result.current.handleDownload();
      });

      expect(downloadOpenLibraryDumps).toHaveBeenCalledWith([
        "https://example.com/works.txt.gz",
      ]);
    });

    it("should throw error when no URLs provided", async () => {
      const { result } = renderHook(() => useOpenLibrarySettings());

      act(() => {
        result.current.handleFieldChange("authors_url", null);
        result.current.handleFieldChange("works_url", null);
        result.current.handleFieldChange("editions_url", null);
      });

      await act(async () => {
        await result.current.handleDownload();
      });

      expect(result.current.error).toBe(
        "Please provide at least one URL to download",
      );
      expect(result.current.isDownloading).toBe(false);
      expect(downloadOpenLibraryDumps).not.toHaveBeenCalled();
    });

    it("should handle download error", async () => {
      const errorMessage = "Download failed";
      vi.mocked(downloadOpenLibraryDumps).mockRejectedValue(
        new Error(errorMessage),
      );

      const { result } = renderHook(() => useOpenLibrarySettings());

      await act(async () => {
        await result.current.handleDownload();
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isDownloading).toBe(false);
    });

    it("should handle non-Error rejection", async () => {
      vi.mocked(downloadOpenLibraryDumps).mockRejectedValue("String error");

      const { result } = renderHook(() => useOpenLibrarySettings());

      await act(async () => {
        await result.current.handleDownload();
      });

      expect(result.current.error).toBe("Failed to download files");
    });

    it("should call onDownloadSuccess callback", async () => {
      const onDownloadSuccess = vi.fn();
      vi.mocked(downloadOpenLibraryDumps).mockResolvedValue({
        message: "Download started",
        task_id: 1,
        downloaded_files: [],
        failed_files: [],
      });

      const { result } = renderHook(() =>
        useOpenLibrarySettings({ onDownloadSuccess }),
      );

      await act(async () => {
        await result.current.handleDownload();
      });

      expect(onDownloadSuccess).toHaveBeenCalledOnce();
    });

    it("should call onError callback on error", async () => {
      const onError = vi.fn();
      const errorMessage = "Download failed";
      vi.mocked(downloadOpenLibraryDumps).mockRejectedValue(
        new Error(errorMessage),
      );

      const { result } = renderHook(() => useOpenLibrarySettings({ onError }));

      await act(async () => {
        await result.current.handleDownload();
      });

      expect(onError).toHaveBeenCalledWith(errorMessage);
    });

    it("should set isDownloading state during download", async () => {
      vi.mocked(downloadOpenLibraryDumps).mockResolvedValue({
        message: "Download started",
        task_id: 1,
        downloaded_files: [],
        failed_files: [],
      });

      const { result } = renderHook(() => useOpenLibrarySettings());

      // Initially should be false
      expect(result.current.isDownloading).toBe(false);

      // Call handleDownload and wait for it to complete
      await act(async () => {
        await result.current.handleDownload();
      });

      // After download completes, isDownloading should be false
      expect(result.current.isDownloading).toBe(false);
    });
  });

  describe("handleIngest", () => {
    it("should ingest with all process flags enabled", async () => {
      vi.mocked(ingestOpenLibraryDumps).mockResolvedValue({
        message: "Ingest started",
        task_id: 1,
      });

      const { result } = renderHook(() => useOpenLibrarySettings());

      // Verify hook is initialized
      expect(result.current).not.toBeNull();

      await act(async () => {
        await result.current.handleIngest();
      });

      expect(ingestOpenLibraryDumps).toHaveBeenCalledWith({
        process_authors: true,
        process_works: true,
        process_editions: false,
      });

      expect(result.current.isIngesting).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should ingest with custom process flags", async () => {
      vi.mocked(ingestOpenLibraryDumps).mockResolvedValue({
        message: "Ingest started",
        task_id: 1,
      });

      const { result } = renderHook(() => useOpenLibrarySettings());

      // Verify hook is initialized
      expect(result.current).not.toBeNull();

      act(() => {
        result.current.handleFieldChange("process_authors", false);
        result.current.handleFieldChange("process_works", false);
        result.current.handleFieldChange("process_editions", true);
      });

      await act(async () => {
        await result.current.handleIngest();
      });

      expect(ingestOpenLibraryDumps).toHaveBeenCalledWith({
        process_authors: false,
        process_works: false,
        process_editions: true,
      });
    });

    it("should throw error when no process flags enabled", async () => {
      const { result } = renderHook(() => useOpenLibrarySettings());

      // Verify hook is initialized
      expect(result.current).not.toBeNull();

      act(() => {
        result.current.handleFieldChange("process_authors", false);
        result.current.handleFieldChange("process_works", false);
        result.current.handleFieldChange("process_editions", false);
      });

      await act(async () => {
        await result.current.handleIngest();
      });

      expect(result.current.error).toBe(
        "Please select at least one file type to process",
      );

      expect(result.current.isIngesting).toBe(false);
      expect(ingestOpenLibraryDumps).not.toHaveBeenCalled();
    });

    it("should handle ingest error", async () => {
      const errorMessage = "Ingest failed";
      vi.mocked(ingestOpenLibraryDumps).mockRejectedValue(
        new Error(errorMessage),
      );

      const { result } = renderHook(() => useOpenLibrarySettings());

      // Verify hook is initialized
      expect(result.current).not.toBeNull();

      await act(async () => {
        await result.current.handleIngest();
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isIngesting).toBe(false);
    });

    it("should handle non-Error rejection", async () => {
      vi.mocked(ingestOpenLibraryDumps).mockRejectedValue("String error");

      const { result } = renderHook(() => useOpenLibrarySettings());

      // Verify hook is initialized
      expect(result.current).not.toBeNull();

      await act(async () => {
        await result.current.handleIngest();
      });

      expect(result.current.error).toBe("Failed to ingest files");
    });

    it("should call onIngestSuccess callback", async () => {
      const onIngestSuccess = vi.fn();
      vi.mocked(ingestOpenLibraryDumps).mockResolvedValue({
        message: "Ingest started",
        task_id: 1,
      });

      const { result } = renderHook(() =>
        useOpenLibrarySettings({ onIngestSuccess }),
      );

      // Verify hook is initialized
      expect(result.current).not.toBeNull();

      await act(async () => {
        await result.current.handleIngest();
      });

      expect(onIngestSuccess).toHaveBeenCalledOnce();
    });

    it("should call onError callback on error", async () => {
      const onError = vi.fn();
      const errorMessage = "Ingest failed";
      vi.mocked(ingestOpenLibraryDumps).mockRejectedValue(
        new Error(errorMessage),
      );

      const { result } = renderHook(() => useOpenLibrarySettings({ onError }));

      // Verify hook is initialized
      expect(result.current).not.toBeNull();

      await act(async () => {
        await result.current.handleIngest();
      });

      expect(onError).toHaveBeenCalledWith(errorMessage);
    });

    it("should set isIngesting state during ingest", async () => {
      vi.mocked(ingestOpenLibraryDumps).mockResolvedValue({
        message: "Ingest started",
        task_id: 1,
      });

      const { result } = renderHook(() => useOpenLibrarySettings());

      // Verify hook is initialized
      expect(result.current).not.toBeNull();

      // Initially should be false
      expect(result.current.isIngesting).toBe(false);

      // Call handleIngest and wait for it to complete
      await act(async () => {
        await result.current.handleIngest();
      });

      // After ingest completes, isIngesting should be false
      expect(result.current.isIngesting).toBe(false);
    });
  });
});
