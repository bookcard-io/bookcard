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
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Permission, RolePermission } from "@/services/roleService";
import { usePermissionForm } from "./usePermissionForm";

vi.mock("@/utils/permissionValidation", () => ({
  validatePermissionForm: vi.fn(),
  validateConditionJson: vi.fn(),
}));

import {
  validateConditionJson,
  validatePermissionForm,
} from "@/utils/permissionValidation";

describe("usePermissionForm", () => {
  let mockOnSubmit: ReturnType<typeof vi.fn<(data: unknown) => Promise<void>>>;
  let mockOnError: ReturnType<typeof vi.fn<(error: string) => void>>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnSubmit = vi.fn<(data: unknown) => Promise<void>>();
    mockOnError = vi.fn<(error: string) => void>();
    vi.mocked(validatePermissionForm).mockReturnValue({});
    vi.mocked(validateConditionJson).mockReturnValue(undefined);
  });

  it("should initialize with empty form data when no permission provided", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    expect(result.current.formData).toEqual({
      name: "",
      description: "",
      resource: "",
      action: "",
      condition: "",
    });
    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.errors).toEqual({});
    expect(result.current.generalError).toBeNull();
  });

  it("should initialize with permission data when permission is provided", () => {
    const permission: Permission = {
      id: 1,
      name: "Test Permission",
      description: "Test Description",
      resource: "test-resource",
      action: "test-action",
    };

    const { result } = renderHook(() => usePermissionForm({ permission }));

    expect(result.current.formData).toEqual({
      name: "Test Permission",
      description: "Test Description",
      resource: "test-resource",
      action: "test-action",
      condition: "",
    });
  });

  it("should initialize with role permission condition when rolePermission is provided", () => {
    const rolePermission: RolePermission = {
      id: 1,
      permission: {
        id: 1,
        name: "Test Permission",
        description: "Test Description",
        resource: "test-resource",
        action: "test-action",
      },
      assigned_at: "2025-01-01",
      condition: { key: "value" },
    };

    const { result } = renderHook(() => usePermissionForm({ rolePermission }));

    expect(result.current.formData.condition).toBe(
      JSON.stringify({ key: "value" }, null, 2),
    );
  });

  it("should update name when setName is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    act(() => {
      result.current.setName("New Name");
    });

    expect(result.current.formData.name).toBe("New Name");
  });

  it("should clear name error when setName is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    // Set an error first
    act(() => {
      result.current.setName("");
    });

    vi.mocked(validatePermissionForm).mockReturnValue({
      name: "Name is required",
    });

    act(() => {
      result.current.validate();
    });

    expect(result.current.errors.name).toBe("Name is required");

    // Clear error by setting name
    act(() => {
      result.current.setName("Valid Name");
    });

    expect(result.current.errors.name).toBeUndefined();
  });

  it("should update description when setDescription is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    act(() => {
      result.current.setDescription("New Description");
    });

    expect(result.current.formData.description).toBe("New Description");
  });

  it("should clear description error when setDescription is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    vi.mocked(validatePermissionForm).mockReturnValue({
      description: "Description too long",
    });

    act(() => {
      result.current.validate();
    });

    expect(result.current.errors.description).toBe("Description too long");

    act(() => {
      result.current.setDescription("Valid Description");
    });

    expect(result.current.errors.description).toBeUndefined();
  });

  it("should update resource when setResource is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    act(() => {
      result.current.setResource("new-resource");
    });

    expect(result.current.formData.resource).toBe("new-resource");
  });

  it("should clear resource error when setResource is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    vi.mocked(validatePermissionForm).mockReturnValue({
      resource: "Resource is required",
    });

    act(() => {
      result.current.validate();
    });

    expect(result.current.errors.resource).toBe("Resource is required");

    act(() => {
      result.current.setResource("valid-resource");
    });

    expect(result.current.errors.resource).toBeUndefined();
  });

  it("should update action when setAction is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    act(() => {
      result.current.setAction("new-action");
    });

    expect(result.current.formData.action).toBe("new-action");
  });

  it("should clear action error when setAction is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    vi.mocked(validatePermissionForm).mockReturnValue({
      action: "Action is required",
    });

    act(() => {
      result.current.validate();
    });

    expect(result.current.errors.action).toBe("Action is required");

    act(() => {
      result.current.setAction("valid-action");
    });

    expect(result.current.errors.action).toBeUndefined();
  });

  it("should update condition when setCondition is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    act(() => {
      result.current.setCondition('{"key": "value"}');
    });

    expect(result.current.formData.condition).toBe('{"key": "value"}');
  });

  it("should validate condition JSON when setCondition is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    vi.mocked(validateConditionJson).mockReturnValue("Invalid JSON");

    act(() => {
      result.current.setCondition("invalid json");
    });

    expect(validateConditionJson).toHaveBeenCalledWith("invalid json");
    expect(result.current.errors.condition).toBe("Invalid JSON");
  });

  it("should clear condition error when valid JSON is set", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    vi.mocked(validateConditionJson).mockReturnValueOnce("Invalid JSON");

    act(() => {
      result.current.setCondition("invalid");
    });

    expect(result.current.errors.condition).toBe("Invalid JSON");

    vi.mocked(validateConditionJson).mockReturnValueOnce(undefined);

    act(() => {
      result.current.setCondition('{"valid": true}');
    });

    expect(result.current.errors.condition).toBeUndefined();
  });

  it("should clear field error when clearFieldError is called", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    vi.mocked(validatePermissionForm).mockReturnValue({
      name: "Name is required",
      description: "Description too long",
    });

    act(() => {
      result.current.validate();
    });

    expect(result.current.errors.name).toBe("Name is required");
    expect(result.current.errors.description).toBe("Description too long");

    act(() => {
      result.current.clearFieldError("name");
    });

    expect(result.current.errors.name).toBeUndefined();
    expect(result.current.errors.description).toBe("Description too long");
  });

  it("should validate form and return true when valid", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    vi.mocked(validatePermissionForm).mockReturnValue({});

    act(() => {
      const isValid = result.current.validate();
      expect(isValid).toBe(true);
    });

    expect(result.current.errors).toEqual({});
  });

  it("should validate form and return false when invalid", () => {
    const { result } = renderHook(() => usePermissionForm({}));

    vi.mocked(validatePermissionForm).mockReturnValue({
      name: "Name is required",
    });

    act(() => {
      const isValid = result.current.validate();
      expect(isValid).toBe(false);
    });

    expect(result.current.errors.name).toBe("Name is required");
  });

  it("should not submit when validation fails", async () => {
    const { result } = renderHook(() =>
      usePermissionForm({
        onSubmit: mockOnSubmit,
      }),
    );

    vi.mocked(validatePermissionForm).mockReturnValue({
      name: "Name is required",
    });

    let success = false;
    await act(async () => {
      success = await result.current.handleSubmit();
    });

    expect(success).toBe(false);
    expect(mockOnSubmit).not.toHaveBeenCalled();
    expect(result.current.isSubmitting).toBe(false);
  });

  it("should not submit when onSubmit is not provided", async () => {
    const { result } = renderHook(() => usePermissionForm({}));

    vi.mocked(validatePermissionForm).mockReturnValue({});

    let success = true;
    await act(async () => {
      success = await result.current.handleSubmit();
    });

    expect(success).toBe(false);
    expect(result.current.isSubmitting).toBe(false);
  });

  it("should submit form successfully when valid", async () => {
    const { result } = renderHook(() =>
      usePermissionForm({
        onSubmit: mockOnSubmit,
      }),
    );

    vi.mocked(validatePermissionForm).mockReturnValue({});
    mockOnSubmit.mockResolvedValue(undefined);

    let success = false;
    await act(async () => {
      success = await result.current.handleSubmit();
    });

    expect(success).toBe(true);
    expect(mockOnSubmit).toHaveBeenCalledWith(result.current.formData);
    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.generalError).toBeNull();
  });

  it("should handle submission error", async () => {
    const { result } = renderHook(() =>
      usePermissionForm({
        onSubmit: mockOnSubmit,
        onError: mockOnError,
      }),
    );

    vi.mocked(validatePermissionForm).mockReturnValue({});
    const error = new Error("Submission failed");
    mockOnSubmit.mockRejectedValue(error);

    let success = true;
    await act(async () => {
      success = await result.current.handleSubmit();
    });

    expect(success).toBe(false);
    expect(result.current.generalError).toBe("Submission failed");
    expect(mockOnError).toHaveBeenCalledWith("Submission failed");
    expect(result.current.isSubmitting).toBe(false);
  });

  it("should handle non-Error exception", async () => {
    const { result } = renderHook(() =>
      usePermissionForm({
        onSubmit: mockOnSubmit,
        onError: mockOnError,
      }),
    );

    vi.mocked(validatePermissionForm).mockReturnValue({});
    mockOnSubmit.mockRejectedValue("String error");

    let success = true;
    await act(async () => {
      success = await result.current.handleSubmit();
    });

    expect(success).toBe(false);
    expect(result.current.generalError).toBe("Failed to save permission");
    expect(mockOnError).toHaveBeenCalledWith("Failed to save permission");
  });

  it("should reset form to initial values", () => {
    const permission: Permission = {
      id: 1,
      name: "Initial Name",
      description: "Initial Description",
      resource: "initial-resource",
      action: "initial-action",
    };

    const { result } = renderHook(() => usePermissionForm({ permission }));

    act(() => {
      result.current.setName("Changed Name");
      result.current.setDescription("Changed Description");
    });

    vi.mocked(validatePermissionForm).mockReturnValue({
      name: "Name is required",
    });

    act(() => {
      result.current.validate();
    });

    expect(result.current.formData.name).toBe("Changed Name");
    expect(result.current.errors.name).toBe("Name is required");

    act(() => {
      result.current.reset();
    });

    expect(result.current.formData.name).toBe("Initial Name");
    expect(result.current.formData.description).toBe("Initial Description");
    expect(result.current.errors).toEqual({});
    expect(result.current.generalError).toBeNull();
  });

  it("should set isSubmitting to true during submission", async () => {
    const { result } = renderHook(() =>
      usePermissionForm({
        onSubmit: mockOnSubmit,
      }),
    );

    vi.mocked(validatePermissionForm).mockReturnValue({});
    let resolveSubmit: () => void;
    const submitPromise = new Promise<void>((resolve) => {
      resolveSubmit = resolve;
    });
    mockOnSubmit.mockReturnValue(submitPromise);

    const submitPromise2 = result.current.handleSubmit();

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    expect(result.current.isSubmitting).toBe(true);

    await act(async () => {
      resolveSubmit?.();
      await submitPromise2;
    });

    expect(result.current.isSubmitting).toBe(false);
  });
});
