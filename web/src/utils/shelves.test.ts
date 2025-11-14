import { beforeEach, describe, expect, it, vi } from "vitest";
import { getShelfCoverPictureUrl } from "@/services/shelfService";
import type { Shelf } from "@/types/shelf";
import {
  deduplicateShelves,
  getShelfCoverUrlWithCacheBuster,
  processShelves,
  sortShelvesByCreatedAt,
} from "./shelves";

// Mock the service function
vi.mock("@/services/shelfService", () => ({
  getShelfCoverPictureUrl: vi.fn(
    (id: number) => `/api/shelves/${id}/cover-picture`,
  ),
}));

describe("shelves utils", () => {
  const createMockShelf = (
    id: number,
    created_at: string,
    cover_picture: string | null = null,
  ): Shelf =>
    ({
      id,
      uuid: `uuid-${id}`,
      name: `Shelf ${id}`,
      description: null,
      cover_picture,
      is_public: false,
      is_active: true,
      user_id: 1,
      library_id: 1,
      created_at,
      updated_at: "2024-01-01T00:00:00Z",
      last_modified: "2024-01-01T00:00:00Z",
      book_count: 0,
    }) as Shelf;

  describe("getShelfCoverUrlWithCacheBuster", () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it("should generate URL with cache buster using current time", () => {
      const shelfId = 1;
      const result = getShelfCoverUrlWithCacheBuster(shelfId);
      expect(getShelfCoverPictureUrl).toHaveBeenCalledWith(shelfId);
      expect(result).toMatch(/^\/api\/shelves\/1\/cover-picture\?v=\d+$/);
    });

    it("should generate URL with provided cache buster", () => {
      const shelfId = 1;
      const cacheBuster = 1234567890;
      const result = getShelfCoverUrlWithCacheBuster(shelfId, cacheBuster);
      expect(getShelfCoverPictureUrl).toHaveBeenCalledWith(shelfId);
      expect(result).toBe(`/api/shelves/1/cover-picture?v=${cacheBuster}`);
    });
  });

  describe("deduplicateShelves", () => {
    it("should return empty array for empty input", () => {
      expect(deduplicateShelves([])).toEqual([]);
    });

    it("should return same array for unique shelves", () => {
      const shelves = [
        createMockShelf(1, "2024-01-01T00:00:00Z"),
        createMockShelf(2, "2024-01-02T00:00:00Z"),
      ];
      const result = deduplicateShelves(shelves);
      expect(result).toEqual(shelves);
    });

    it("should remove duplicate shelves by ID", () => {
      const shelf1 = createMockShelf(1, "2024-01-01T00:00:00Z");
      const shelf2 = createMockShelf(2, "2024-01-02T00:00:00Z");
      const shelf1Duplicate = createMockShelf(1, "2024-01-03T00:00:00Z");
      const shelves = [shelf1, shelf2, shelf1Duplicate];
      const result = deduplicateShelves(shelves);
      expect(result).toHaveLength(2);
      expect(result[0]).toBe(shelf1); // First occurrence is kept
      expect(result[1]).toBe(shelf2);
    });

    it("should apply shelf data overrides", () => {
      const shelf1 = createMockShelf(
        1,
        "2024-01-01T00:00:00Z",
        "old-cover.jpg",
      );
      const shelf2 = createMockShelf(2, "2024-01-02T00:00:00Z");
      const shelves = [shelf1, shelf2];
      const overrides = new Map<number, Partial<Shelf>>([
        [1, { name: "Updated Shelf", cover_picture: "new-cover.jpg" }],
      ]);
      const result = deduplicateShelves(shelves, overrides);
      expect(result).toHaveLength(2);
      expect(result[0]?.name).toBe("Updated Shelf");
      expect(result[0]?.cover_picture).toBe("new-cover.jpg");
      expect(result[0]?.id).toBe(1);
      expect(result[1]).toBe(shelf2); // No override, original object
    });

    it("should not create new objects for shelves without overrides", () => {
      const shelf1 = createMockShelf(1, "2024-01-01T00:00:00Z");
      const shelf2 = createMockShelf(2, "2024-01-02T00:00:00Z");
      const shelves = [shelf1, shelf2];
      const overrides = new Map<number, Partial<Shelf>>([
        [1, { name: "Updated Shelf" }],
      ]);
      const result = deduplicateShelves(shelves, overrides);
      expect(result[0]).not.toBe(shelf1); // New object created for override
      expect(result[1]).toBe(shelf2); // Original object kept
    });

    it("should handle multiple duplicates", () => {
      const shelf1 = createMockShelf(1, "2024-01-01T00:00:00Z");
      const shelf2 = createMockShelf(2, "2024-01-02T00:00:00Z");
      const shelf1Duplicate = createMockShelf(1, "2024-01-03T00:00:00Z");
      const shelf2Duplicate = createMockShelf(2, "2024-01-04T00:00:00Z");
      const shelves = [shelf1, shelf2, shelf1Duplicate, shelf2Duplicate];
      const result = deduplicateShelves(shelves);
      expect(result).toHaveLength(2);
      expect(result[0]?.id).toBe(1);
      expect(result[1]?.id).toBe(2);
    });
  });

  describe("sortShelvesByCreatedAt", () => {
    it("should return empty array for empty input", () => {
      expect(sortShelvesByCreatedAt([])).toEqual([]);
    });

    it("should sort shelves by created_at in descending order", () => {
      const shelf1 = createMockShelf(1, "2024-01-01T00:00:00Z");
      const shelf2 = createMockShelf(2, "2024-01-03T00:00:00Z");
      const shelf3 = createMockShelf(3, "2024-01-02T00:00:00Z");
      const shelves = [shelf1, shelf2, shelf3];
      const result = sortShelvesByCreatedAt(shelves);
      expect(result).toHaveLength(3);
      expect(result[0]?.id).toBe(2); // Newest first
      expect(result[1]?.id).toBe(3);
      expect(result[2]?.id).toBe(1); // Oldest last
    });

    it("should not mutate original array", () => {
      const shelf1 = createMockShelf(1, "2024-01-01T00:00:00Z");
      const shelf2 = createMockShelf(2, "2024-01-02T00:00:00Z");
      const shelves = [shelf1, shelf2];
      const originalOrder = [...shelves];
      sortShelvesByCreatedAt(shelves);
      expect(shelves).toEqual(originalOrder);
    });
  });

  describe("processShelves", () => {
    it("should deduplicate, apply overrides, and sort", () => {
      const shelf1 = createMockShelf(1, "2024-01-01T00:00:00Z");
      const shelf2 = createMockShelf(2, "2024-01-03T00:00:00Z");
      const shelf3 = createMockShelf(3, "2024-01-02T00:00:00Z");
      const shelf1Duplicate = createMockShelf(1, "2024-01-04T00:00:00Z");
      const shelves = [shelf1, shelf2, shelf3, shelf1Duplicate];
      const overrides = new Map<number, Partial<Shelf>>([
        [1, { name: "Updated Shelf" }],
      ]);
      const result = processShelves(shelves, overrides);
      expect(result).toHaveLength(3); // Deduplicated
      expect(result[0]?.id).toBe(2); // Sorted by created_at descending
      expect(result[1]?.id).toBe(3);
      expect(result[2]?.id).toBe(1);
      expect(result[2]?.name).toBe("Updated Shelf"); // Override applied
    });

    it("should work without overrides", () => {
      const shelf1 = createMockShelf(1, "2024-01-01T00:00:00Z");
      const shelf2 = createMockShelf(2, "2024-01-02T00:00:00Z");
      const shelves = [shelf1, shelf2];
      const result = processShelves(shelves);
      expect(result).toHaveLength(2);
      expect(result[0]?.id).toBe(2); // Sorted descending
      expect(result[1]?.id).toBe(1);
    });
  });
});
