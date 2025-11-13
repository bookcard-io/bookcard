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
import { describe, expect, it, vi } from "vitest";
import { useShelfForm } from "./useShelfForm";

describe("useShelfForm", () => {
  it("should initialize with default values", () => {
    const { result } = renderHook(() => useShelfForm());

    expect(result.current.name).toBe("");
    expect(result.current.description).toBe("");
    expect(result.current.isPublic).toBe(false);
    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.errors).toEqual({});
  });

  it("should initialize with provided initial values", () => {
    const { result } = renderHook(() =>
      useShelfForm({
        initialName: "Test Shelf",
        initialDescription: "Test Description",
        initialIsPublic: true,
      }),
    );

    expect(result.current.name).toBe("Test Shelf");
    expect(result.current.description).toBe("Test Description");
    expect(result.current.isPublic).toBe(true);
  });

  it("should handle null initial description", () => {
    const { result } = renderHook(() =>
      useShelfForm({
        initialDescription: null,
      }),
    );

    expect(result.current.description).toBe("");
  });

  it("should update name", () => {
    const { result } = renderHook(() => useShelfForm());

    act(() => {
      result.current.setName("New Name");
    });

    expect(result.current.name).toBe("New Name");
  });

  it("should update description", () => {
    const { result } = renderHook(() => useShelfForm());

    act(() => {
      result.current.setDescription("New Description");
    });

    expect(result.current.description).toBe("New Description");
  });

  it("should update isPublic", () => {
    const { result } = renderHook(() => useShelfForm());

    act(() => {
      result.current.setIsPublic(true);
    });

    expect(result.current.isPublic).toBe(true);
  });

  describe("validation", () => {
    it("should validate empty name", async () => {
      const { result } = renderHook(() => useShelfForm());

      await act(async () => {
        const isValid = await result.current.handleSubmit();
        expect(isValid).toBe(false);
      });

      expect(result.current.errors.name).toBe("Shelf name is required");
    });

    it("should validate name with only whitespace", async () => {
      const { result } = renderHook(() => useShelfForm());

      act(() => {
        result.current.setName("   ");
      });

      await act(async () => {
        const isValid = await result.current.handleSubmit();
        expect(isValid).toBe(false);
      });

      expect(result.current.errors.name).toBe("Shelf name is required");
    });

    it("should validate name length", async () => {
      const { result } = renderHook(() => useShelfForm());

      act(() => {
        result.current.setName("a".repeat(256));
      });

      await act(async () => {
        const isValid = await result.current.handleSubmit();
        expect(isValid).toBe(false);
      });

      expect(result.current.errors.name).toBe(
        "Shelf name must be 255 characters or less",
      );
    });

    it("should validate description length", async () => {
      const { result } = renderHook(() => useShelfForm());

      act(() => {
        result.current.setName("Valid Name");
        result.current.setDescription("a".repeat(5001));
      });

      await act(async () => {
        const isValid = await result.current.handleSubmit();
        expect(isValid).toBe(false);
      });

      expect(result.current.errors.description).toBe(
        "Description must be 5000 characters or less",
      );
    });

    it("should pass validation with valid data", async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() =>
        useShelfForm({
          onSubmit,
        }),
      );

      act(() => {
        result.current.setName("Valid Name");
        result.current.setDescription("Valid Description");
      });

      await act(async () => {
        const isValid = await result.current.handleSubmit();
        expect(isValid).toBe(true);
      });

      expect(result.current.errors).toEqual({});
      expect(onSubmit).toHaveBeenCalledWith({
        name: "Valid Name",
        description: "Valid Description",
        is_public: false,
      });
    });
  });

  describe("handleSubmit", () => {
    it("should call onSubmit with trimmed values", async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() =>
        useShelfForm({
          onSubmit,
        }),
      );

      act(() => {
        result.current.setName("  Trimmed Name  ");
        result.current.setDescription("  Trimmed Description  ");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(onSubmit).toHaveBeenCalledWith({
        name: "Trimmed Name",
        description: "Trimmed Description",
        is_public: false,
      });
    });

    it("should convert empty description to null", async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() =>
        useShelfForm({
          onSubmit,
        }),
      );

      act(() => {
        result.current.setName("Valid Name");
        result.current.setDescription("   ");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(onSubmit).toHaveBeenCalledWith({
        name: "Valid Name",
        description: null,
        is_public: false,
      });
    });

    it("should set isSubmitting during submission", async () => {
      let resolvePromise: () => void;
      const promise = new Promise<void>((resolve) => {
        resolvePromise = resolve;
      });
      const onSubmit = vi.fn().mockReturnValue(promise);

      const { result } = renderHook(() =>
        useShelfForm({
          onSubmit,
        }),
      );

      act(() => {
        result.current.setName("Valid Name");
      });

      act(() => {
        void result.current.handleSubmit();
      });

      expect(result.current.isSubmitting).toBe(true);

      act(() => {
        if (resolvePromise) {
          resolvePromise();
        }
      });

      await act(async () => {
        await promise;
      });

      expect(result.current.isSubmitting).toBe(false);
    });

    it("should handle submission error", async () => {
      const errorMessage = "Submission failed";
      const onSubmit = vi.fn().mockRejectedValue(new Error(errorMessage));
      const onError = vi.fn();

      const { result } = renderHook(() =>
        useShelfForm({
          onSubmit,
          onError,
        }),
      );

      act(() => {
        result.current.setName("Valid Name");
      });

      await act(async () => {
        const isValid = await result.current.handleSubmit();
        expect(isValid).toBe(false);
      });

      expect(result.current.errors.name).toBe(errorMessage);
      expect(onError).toHaveBeenCalledWith(errorMessage);
    });

    it("should handle non-Error rejection", async () => {
      const onSubmit = vi.fn().mockRejectedValue("String error");
      const onError = vi.fn();

      const { result } = renderHook(() =>
        useShelfForm({
          onSubmit,
          onError,
        }),
      );

      act(() => {
        result.current.setName("Valid Name");
      });

      await act(async () => {
        const isValid = await result.current.handleSubmit();
        expect(isValid).toBe(false);
      });

      expect(result.current.errors.name).toBe("Failed to save shelf");
      expect(onError).toHaveBeenCalledWith("Failed to save shelf");
    });

    it("should clear errors before submission", async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() =>
        useShelfForm({
          onSubmit,
        }),
      );

      act(() => {
        result.current.setName("");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(result.current.errors.name).toBe("Shelf name is required");

      act(() => {
        result.current.setName("Valid Name");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(result.current.errors).toEqual({});
    });
  });

  describe("reset", () => {
    it("should reset form to initial values", () => {
      const { result } = renderHook(() =>
        useShelfForm({
          initialName: "Initial Name",
          initialDescription: "Initial Description",
          initialIsPublic: true,
        }),
      );

      act(() => {
        result.current.setName("Changed Name");
        result.current.setDescription("Changed Description");
        result.current.setIsPublic(false);
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.name).toBe("Initial Name");
      expect(result.current.description).toBe("Initial Description");
      expect(result.current.isPublic).toBe(true);
      expect(result.current.errors).toEqual({});
      expect(result.current.isSubmitting).toBe(false);
    });
  });
});
