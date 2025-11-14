import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchLibraryStats, type LibraryStats } from "./libraryStatsService";

describe("libraryStatsService", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should fetch library stats successfully", async () => {
    const mockStats: LibraryStats = {
      total_books: 100,
      total_series: 20,
      total_authors: 50,
      total_tags: 30,
      total_ratings: 80,
      total_content_size: 5000000,
    };

    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockStats),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const result = await fetchLibraryStats(1);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/admin/libraries/1/stats",
      { cache: "no-store" },
    );
    expect(result).toEqual(mockStats);
  });

  it("should return null when response is not ok", async () => {
    const mockFetchResponse = {
      ok: false,
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const result = await fetchLibraryStats(1);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/admin/libraries/1/stats",
      { cache: "no-store" },
    );
    expect(result).toBeNull();
  });

  it("should return null when fetch throws an error", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Network error"),
    );

    const result = await fetchLibraryStats(1);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/admin/libraries/1/stats",
      { cache: "no-store" },
    );
    expect(result).toBeNull();
  });
});
