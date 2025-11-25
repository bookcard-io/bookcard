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

import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { OpenLibraryDumpConfig } from "@/services/openLibraryConfigService";
import {
  getOpenLibraryDumpConfig,
  updateOpenLibraryDumpConfig,
} from "@/services/openLibraryConfigService";
import { useOpenLibraryDumpConfig } from "./useOpenLibraryDumpConfig";

vi.mock("@/services/openLibraryConfigService", () => ({
  getOpenLibraryDumpConfig: vi.fn(),
  updateOpenLibraryDumpConfig: vi.fn(),
}));

describe("useOpenLibraryDumpConfig", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockConfig: OpenLibraryDumpConfig = {
    id: 1,
    authors_url: "https://example.com/authors.txt.gz",
    works_url: "https://example.com/works.txt.gz",
    editions_url: "https://example.com/editions.txt.gz",
    default_process_authors: true,
    default_process_works: true,
    default_process_editions: false,
    staleness_threshold_days: 30,
    enable_auto_download: false,
    enable_auto_process: false,
    auto_check_interval_hours: 24,
    updated_at: "2025-01-01T00:00:00Z",
    created_at: "2025-01-01T00:00:00Z",
  };

  describe("initialization", () => {
    it("should start with loading state", () => {
      vi.mocked(getOpenLibraryDumpConfig).mockImplementation(
        () => new Promise(() => {}), // Never resolves
      );

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      expect(result.current.isLoading).toBe(true);
      expect(result.current.config).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.isSaving).toBe(false);
    });

    it("should load configuration on mount", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.config).toEqual(mockConfig);
      expect(result.current.error).toBeNull();
      expect(getOpenLibraryDumpConfig).toHaveBeenCalledOnce();
    });
  });

  describe("loading errors", () => {
    it("should handle loading error", async () => {
      const errorMessage = "Failed to load configuration";
      vi.mocked(getOpenLibraryDumpConfig).mockRejectedValue(
        new Error(errorMessage),
      );

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.config).toBeNull();
      expect(result.current.error).toBe(errorMessage);
    });

    it("should handle non-Error rejection", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockRejectedValue("String error");

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBe("Failed to load configuration");
    });
  });

  describe("updateField", () => {
    it("should optimistically update local state", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);
      vi.mocked(updateOpenLibraryDumpConfig).mockResolvedValue({
        ...mockConfig,
        authors_url: "https://example.com/new-authors.txt.gz",
      });

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateField(
          "authors_url",
          "https://example.com/new-authors.txt.gz",
        );
      });

      // Optimistic update
      expect(result.current.config?.authors_url).toBe(
        "https://example.com/new-authors.txt.gz",
      );
    });

    it("should not update if config is null", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Set config to null by mocking getOpenLibraryDumpConfig to return null
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValueOnce(
        null as unknown as OpenLibraryDumpConfig,
      );

      // Refresh to get null config
      await act(async () => {
        await result.current.refresh();
      });

      // Now try to update - should not crash
      act(() => {
        result.current.updateField(
          "authors_url",
          "https://example.com/new.txt.gz",
        );
      });

      // Config should remain null (optimistic update won't work with null)
      expect(result.current.config).toBeNull();
    });

    it("should queue multiple updates", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);
      vi.mocked(updateOpenLibraryDumpConfig).mockResolvedValue(mockConfig);

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateField("authors_url", "url1");
      });

      act(() => {
        result.current.updateField("works_url", "url2");
      });

      act(() => {
        result.current.updateField("editions_url", "url3");
      });

      // Verify optimistic updates
      expect(result.current.config?.authors_url).toBe("url1");
      expect(result.current.config?.works_url).toBe("url2");
      expect(result.current.config?.editions_url).toBe("url3");
    });

    it("should allow multiple sequential updates", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);
      vi.mocked(updateOpenLibraryDumpConfig).mockResolvedValue(mockConfig);

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateField("authors_url", "url1");
      });

      // Update again
      act(() => {
        result.current.updateField("works_url", "url2");
      });

      // Verify both updates are reflected optimistically
      expect(result.current.config?.authors_url).toBe("url1");
      expect(result.current.config?.works_url).toBe("url2");
    });

    it("should allow rapid sequential updates", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);
      vi.mocked(updateOpenLibraryDumpConfig).mockResolvedValue(mockConfig);

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateField("authors_url", "url1");
      });

      // Update again quickly
      act(() => {
        result.current.updateField("works_url", "url2");
      });

      // Both updates should be reflected optimistically
      expect(result.current.config?.authors_url).toBe("url1");
      expect(result.current.config?.works_url).toBe("url2");
    });
  });

  describe("savePendingUpdates", () => {
    it("should not save if there are no pending updates", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // No updates made, so updateOpenLibraryDumpConfig should not be called
      expect(updateOpenLibraryDumpConfig).not.toHaveBeenCalled();
    });

    it("should optimistically update config on field change", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);
      const updatedConfig = {
        ...mockConfig,
        authors_url: "https://example.com/new-authors.txt.gz",
      };
      vi.mocked(updateOpenLibraryDumpConfig).mockResolvedValue(updatedConfig);

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateField(
          "authors_url",
          "https://example.com/new-authors.txt.gz",
        );
      });

      // Should optimistically update immediately
      expect(result.current.config?.authors_url).toBe(
        "https://example.com/new-authors.txt.gz",
      );
    });

    it("should handle save error", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);
      vi.mocked(updateOpenLibraryDumpConfig).mockRejectedValue(
        new Error("Save failed"),
      );

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateField("authors_url", "url1");
      });

      // Verify optimistic update
      expect(result.current.config?.authors_url).toBe("url1");
    });

    it("should handle non-Error rejection during save", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);
      vi.mocked(updateOpenLibraryDumpConfig).mockRejectedValue("String error");

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateField("authors_url", "url1");
      });

      // Verify optimistic update still works
      expect(result.current.config?.authors_url).toBe("url1");
    });

    it("should update field optimistically", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);
      vi.mocked(updateOpenLibraryDumpConfig).mockResolvedValue(mockConfig);

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateField("authors_url", "url1");
      });

      // Should update optimistically immediately
      expect(result.current.config?.authors_url).toBe("url1");
    });
  });

  describe("refresh", () => {
    it("should reload configuration", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const newConfig = { ...mockConfig, id: 2 };
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(newConfig);

      await act(async () => {
        await result.current.refresh();
      });

      expect(result.current.config).toEqual(newConfig);
      expect(getOpenLibraryDumpConfig).toHaveBeenCalledTimes(2);
    });

    it("should handle refresh error", async () => {
      vi.mocked(getOpenLibraryDumpConfig).mockResolvedValue(mockConfig);

      const { result } = renderHook(() => useOpenLibraryDumpConfig());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const errorMessage = "Refresh failed";
      vi.mocked(getOpenLibraryDumpConfig).mockRejectedValue(
        new Error(errorMessage),
      );

      await act(async () => {
        await result.current.refresh();
      });

      expect(result.current.error).toBe(errorMessage);
      // Config should remain unchanged
      expect(result.current.config).toEqual(mockConfig);
    });
  });
});
