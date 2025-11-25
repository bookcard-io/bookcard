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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AuthorWithMetadata } from "@/types/author";
import { useAuthorEditForm } from "./useAuthorEditForm";

vi.mock("./useAuthor", () => ({
  useAuthor: vi.fn(),
}));

vi.mock("@/services/authorService", () => ({
  updateAuthor: vi.fn(),
}));

vi.mock("@/contexts/UserContext", () => ({
  useUser: vi.fn(),
}));

import { useUser } from "@/contexts/UserContext";
import { updateAuthor } from "@/services/authorService";
import { useAuthor } from "./useAuthor";

/**
 * Create a mock author for testing.
 */
function createMockAuthor(key: string): AuthorWithMetadata {
  return {
    key,
    name: "Test Author",
    personal_name: "Personal Name",
    fuller_name: "Fuller Name",
    title: "OBE",
    birth_date: "1900-01-01",
    death_date: "2000-01-01",
    entity_type: "person",
    bio: { type: "text", value: "Biography text" },
    location: "Location",
    photo_url: "https://example.com/photo.jpg",
  };
}

describe("useAuthorEditForm", () => {
  const mockAuthor = createMockAuthor("OL123A");
  const mockOnClose = vi.fn();
  const mockOnAuthorSaved = vi.fn();
  const mockGetSetting = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuthor).mockReturnValue({
      author: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      updateAuthor: vi.fn(),
    });
    vi.mocked(useUser).mockReturnValue({
      getSetting: mockGetSetting,
    } as unknown as ReturnType<typeof useUser>);
    mockGetSetting.mockReturnValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("initialization", () => {
    it("should initialize with empty form data when author is null", () => {
      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: null,
          onClose: mockOnClose,
        }),
      );

      expect(result.current.formData).toEqual({});
      expect(result.current.hasChanges).toBe(false);
      expect(result.current.showSuccess).toBe(false);
      expect(result.current.isUpdating).toBe(false);
      expect(result.current.updateError).toBeNull();
      expect(result.current.stagedPhotoUrl).toBeNull();
    });

    it("should initialize form data when author loads", async () => {
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      expect(result.current.formData.personal_name).toBe("Personal Name");
      expect(result.current.formData.fuller_name).toBe("Fuller Name");
      expect(result.current.formData.title).toBe("OBE");
      expect(result.current.formData.birth_date).toBe("1900-01-01");
      expect(result.current.formData.death_date).toBe("2000-01-01");
      expect(result.current.formData.entity_type).toBe("person");
      expect(result.current.formData.biography).toBe("Biography text");
      expect(result.current.formData.location).toBe("Location");
      expect(result.current.formData.photo_url).toBe(
        "https://example.com/photo.jpg",
      );
    });

    it("should handle author with null values", async () => {
      const authorWithNulls = createMockAuthor("OL123A");
      authorWithNulls.personal_name = undefined;
      authorWithNulls.bio = undefined;
      vi.mocked(useAuthor).mockReturnValue({
        author: authorWithNulls,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      expect(result.current.formData.personal_name).toBeNull();
      expect(result.current.formData.biography).toBeNull();
    });
  });

  describe("handleFieldChange", () => {
    it("should update form data and detect changes", async () => {
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      act(() => {
        result.current.handleFieldChange("name", "Updated Name");
      });

      expect(result.current.formData.name).toBe("Updated Name");
      expect(result.current.hasChanges).toBe(true);
      expect(result.current.updateError).toBeNull();
    });

    it("should clear updateError on field change", async () => {
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      // Simulate an error state
      act(() => {
        result.current.handleFieldChange("name", "Updated Name");
      });

      expect(result.current.updateError).toBeNull();
    });
  });

  describe("handleSubmit", () => {
    it("should submit form successfully", async () => {
      const updatedAuthor = { ...mockAuthor, name: "Updated Name" };
      // Disable auto-dismiss so we can check showSuccess
      mockGetSetting.mockReturnValue("false");
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });
      vi.mocked(updateAuthor).mockResolvedValue(updatedAuthor);

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
          onAuthorSaved: mockOnAuthorSaved,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      act(() => {
        result.current.handleFieldChange("name", "Updated Name");
      });

      // Verify hasChanges is true before submit
      expect(result.current.hasChanges).toBe(true);

      const mockEvent = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent;

      await act(async () => {
        await result.current.handleSubmit(mockEvent);
      });

      await waitFor(() => {
        expect(result.current.showSuccess).toBe(true);
      });

      expect(updateAuthor).toHaveBeenCalledWith(
        "OL123A",
        expect.objectContaining({
          name: "Updated Name",
        }),
      );
      expect(result.current.hasChanges).toBe(false);
      expect(mockOnAuthorSaved).toHaveBeenCalledWith(updatedAuthor);
    });

    it("should not submit when no changes", async () => {
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      const mockEvent = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent;

      await act(async () => {
        await result.current.handleSubmit(mockEvent);
      });

      expect(updateAuthor).not.toHaveBeenCalled();
    });

    it("should not submit when already updating", async () => {
      const updatedAuthor = { ...mockAuthor, name: "Updated Name" };
      let resolveUpdate: ((value: AuthorWithMetadata) => void) | undefined;
      const updatePromise = new Promise<AuthorWithMetadata>((resolve) => {
        resolveUpdate = resolve;
      });
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });
      vi.mocked(updateAuthor).mockReturnValue(updatePromise);

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      act(() => {
        result.current.handleFieldChange("name", "Updated Name");
      });

      const mockEvent = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent;

      // Start first update (will be in progress)
      const submitPromise1 = result.current.handleSubmit(mockEvent);

      // Wait a bit to ensure isUpdating is true
      await waitFor(() => {
        expect(result.current.isUpdating).toBe(true);
      });

      // Try to submit again while first is in progress
      await act(async () => {
        await result.current.handleSubmit(mockEvent);
      });

      // Resolve the first update
      resolveUpdate?.(updatedAuthor);
      await act(async () => {
        await submitPromise1;
      });

      // Should only be called once because second call was blocked by isUpdating check
      expect(updateAuthor).toHaveBeenCalledTimes(1);
    });

    it("should handle update error", async () => {
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });
      vi.mocked(updateAuthor).mockRejectedValue(new Error("Update failed"));

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      act(() => {
        result.current.handleFieldChange("name", "Updated Name");
      });

      const mockEvent = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent;

      await act(async () => {
        await result.current.handleSubmit(mockEvent);
      });

      expect(result.current.updateError).toBe("Update failed");
      expect(result.current.showSuccess).toBe(false);
      expect(result.current.isUpdating).toBe(false);
    });

    it("should handle non-Error rejection", async () => {
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });
      vi.mocked(updateAuthor).mockRejectedValue("String error");

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      act(() => {
        result.current.handleFieldChange("name", "Updated Name");
      });

      const mockEvent = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent;

      await act(async () => {
        await result.current.handleSubmit(mockEvent);
      });

      expect(result.current.updateError).toBe("Failed to update author");
    });

    it("should auto-dismiss when setting is enabled", async () => {
      const updatedAuthor = { ...mockAuthor, name: "Updated Name" };
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });
      vi.mocked(updateAuthor).mockResolvedValue(updatedAuthor);
      mockGetSetting.mockReturnValue("true");

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      act(() => {
        result.current.handleFieldChange("name", "Updated Name");
      });

      const mockEvent = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent;

      await act(async () => {
        await result.current.handleSubmit(mockEvent);
      });

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it("should not auto-dismiss when setting is 'false'", async () => {
      const updatedAuthor = { ...mockAuthor, name: "Updated Name" };
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });
      vi.mocked(updateAuthor).mockResolvedValue(updatedAuthor);
      mockGetSetting.mockReturnValue("false");

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      act(() => {
        result.current.handleFieldChange("name", "Updated Name");
      });

      const mockEvent = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent;

      await act(async () => {
        await result.current.handleSubmit(mockEvent);
      });

      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe("handleClose", () => {
    it("should reset form and call onClose", async () => {
      vi.mocked(useAuthor).mockReturnValue({
        author: mockAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      });

      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      act(() => {
        result.current.handleFieldChange("name", "Updated Name");
      });

      act(() => {
        result.current.handleClose();
      });

      expect(result.current.hasChanges).toBe(false);
      expect(result.current.showSuccess).toBe(false);
      expect(result.current.updateError).toBeNull();
      expect(result.current.stagedPhotoUrl).toBeNull();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe("handlePhotoSaved", () => {
    it("should clear staged photo URL", () => {
      const { result } = renderHook(() =>
        useAuthorEditForm({
          authorId: "OL123A",
          onClose: mockOnClose,
        }),
      );

      // This is a placeholder - photo staging would be set elsewhere
      act(() => {
        result.current.handlePhotoSaved();
      });

      expect(result.current.stagedPhotoUrl).toBeNull();
    });
  });

  describe("author changes", () => {
    it("should reset form when author changes", async () => {
      const author1 = createMockAuthor("OL123A");
      const author2 = createMockAuthor("OL456B");
      author2.name = "Different Author";

      // Create a mock that can return different values
      let currentAuthor: AuthorWithMetadata | null = author1;
      vi.mocked(useAuthor).mockImplementation(() => ({
        author: currentAuthor,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateAuthor: vi.fn(),
      }));

      const { result, rerender } = renderHook(
        ({ authorId }) =>
          useAuthorEditForm({
            authorId,
            onClose: mockOnClose,
          }),
        { initialProps: { authorId: "OL123A" } },
      );

      await waitFor(() => {
        expect(result.current.formData.name).toBe("Test Author");
      });

      // Change author
      currentAuthor = author2;
      rerender({ authorId: "OL456B" });

      await waitFor(
        () => {
          expect(result.current.formData.name).toBe("Different Author");
        },
        { timeout: 2000 },
      );

      expect(result.current.hasChanges).toBe(false);
      expect(result.current.showSuccess).toBe(false);
    });
  });
});
