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
import type { Role, RoleCreate, RoleUpdate } from "@/services/roleService";
import { useRoleForm } from "./useRoleForm";

describe("useRoleForm", () => {
  let mockOnSubmit: ReturnType<
    typeof vi.fn<(data: RoleCreate | RoleUpdate) => Promise<Role>>
  >;
  let mockOnError: ReturnType<typeof vi.fn<(error: string) => void>>;

  beforeEach(() => {
    mockOnSubmit = vi.fn<(data: RoleCreate | RoleUpdate) => Promise<Role>>();
    mockOnError = vi.fn<(error: string) => void>();
  });

  describe("initialization", () => {
    it("should initialize with empty form data in create mode", () => {
      const { result } = renderHook(() => useRoleForm({}));

      expect(result.current.formData).toEqual({
        name: "",
        description: "",
      });
      expect(result.current.isEditMode).toBe(false);
      expect(result.current.isLocked).toBe(false);
      expect(result.current.isSubmitting).toBe(false);
      expect(result.current.errors).toEqual({});
      expect(result.current.generalError).toBeNull();
    });

    it("should initialize with role data in edit mode", () => {
      const role: Role = {
        id: 1,
        name: "Test Role",
        description: "Test Description",
        permissions: [],
      };

      const { result } = renderHook(() => useRoleForm({ role }));

      expect(result.current.formData).toEqual({
        name: "Test Role",
        description: "Test Description",
      });
      expect(result.current.isEditMode).toBe(true);
      expect(result.current.isLocked).toBe(false);
    });

    it("should detect locked role", () => {
      const role: Role = {
        id: 1,
        name: "Admin",
        description: "Admin role",
        permissions: [],
        locked: true,
      };

      const { result } = renderHook(() => useRoleForm({ role }));

      expect(result.current.isLocked).toBe(true);
    });

    it("should handle null role", () => {
      const { result } = renderHook(() => useRoleForm({ role: null }));

      expect(result.current.isEditMode).toBe(false);
      expect(result.current.isLocked).toBe(false);
    });
  });

  describe("form updates", () => {
    it("should update name", () => {
      const { result } = renderHook(() => useRoleForm({}));

      act(() => {
        result.current.setName("New Name");
      });

      expect(result.current.formData.name).toBe("New Name");
    });

    it("should clear name error when updating name", () => {
      const { result } = renderHook(() => useRoleForm({}));

      // Set an error first
      act(() => {
        result.current.validate();
      });
      act(() => {
        result.current.setName("");
      });

      act(() => {
        result.current.setName("Valid Name");
      });

      expect(result.current.errors.name).toBeUndefined();
    });

    it("should update description", () => {
      const { result } = renderHook(() => useRoleForm({}));

      act(() => {
        result.current.setDescription("New Description");
      });

      expect(result.current.formData.description).toBe("New Description");
    });

    it("should clear description error when updating description", () => {
      const { result } = renderHook(() => useRoleForm({}));

      // Set an error first
      act(() => {
        result.current.setDescription("a".repeat(256));
      });
      act(() => {
        result.current.validate();
      });

      act(() => {
        result.current.setDescription("Valid Description");
      });

      expect(result.current.errors.description).toBeUndefined();
    });

    it("should clear field error", () => {
      const { result } = renderHook(() => useRoleForm({}));

      act(() => {
        result.current.validate();
      });

      expect(result.current.errors.name).toBeDefined();

      act(() => {
        result.current.clearFieldError("name");
      });

      expect(result.current.errors.name).toBeUndefined();
    });

    it("should set general error", () => {
      const { result } = renderHook(() => useRoleForm({}));

      act(() => {
        result.current.setGeneralError("Test error");
      });

      expect(result.current.generalError).toBe("Test error");
    });

    it("should clear general error", () => {
      const { result } = renderHook(() => useRoleForm({}));

      act(() => {
        result.current.setGeneralError("Test error");
      });

      act(() => {
        result.current.setGeneralError(null);
      });

      expect(result.current.generalError).toBeNull();
    });
  });

  describe("validation", () => {
    it("should validate form and return true for valid data", () => {
      const { result } = renderHook(() => useRoleForm({}));

      act(() => {
        result.current.setName("Valid Name");
        result.current.setDescription("Valid Description");
      });

      const isValid = result.current.validate();

      expect(isValid).toBe(true);
      expect(result.current.errors).toEqual({});
    });

    it("should validate form and return false for invalid data", () => {
      const { result } = renderHook(() => useRoleForm({}));

      act(() => {
        result.current.setName("");
        result.current.validate();
      });

      expect(result.current.errors.name).toBeDefined();
    });

    it("should validate description length", () => {
      const { result } = renderHook(() => useRoleForm({}));

      act(() => {
        result.current.setName("Valid Name");
        result.current.setDescription("a".repeat(256));
      });

      act(() => {
        const isValid = result.current.validate();
        expect(isValid).toBe(false);
      });

      expect(result.current.errors.description).toBeDefined();
      expect(result.current.errors.description).toBe(
        "Description must be at most 255 characters",
      );
    });
  });

  describe("form submission", () => {
    it("should not submit if validation fails", async () => {
      const { result } = renderHook(() =>
        useRoleForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setName("");
      });

      const success = await result.current.handleSubmit([], []);

      expect(success).toBe(false);
      expect(mockOnSubmit).not.toHaveBeenCalled();
      expect(result.current.isSubmitting).toBe(false);
    });

    it("should not submit if onSubmit is not provided", async () => {
      const { result } = renderHook(() => useRoleForm({}));

      act(() => {
        result.current.setName("Valid Name");
      });

      const success = await result.current.handleSubmit([], []);

      expect(success).toBe(false);
      expect(result.current.isSubmitting).toBe(false);
    });

    it("should submit create form with valid data", async () => {
      const mockRole: Role = {
        id: 1,
        name: "New Role",
        description: "New Description",
        permissions: [],
      };
      mockOnSubmit.mockResolvedValue(mockRole);

      const { result } = renderHook(() =>
        useRoleForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setName("New Role");
        result.current.setDescription("New Description");
      });

      const permissionAssignments = [{ permission_id: 1, condition: null }];

      let success = false;
      await act(async () => {
        success = await result.current.handleSubmit(permissionAssignments);
      });

      expect(success).toBe(true);
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: "New Role",
        description: "New Description",
        permissions: permissionAssignments,
      });
      expect(result.current.isSubmitting).toBe(false);
    });

    it("should submit update form with valid data", async () => {
      const role: Role = {
        id: 1,
        name: "Existing Role",
        description: "Existing Description",
        permissions: [],
      };
      const updatedRole: Role = {
        id: 1,
        name: "Updated Role",
        description: "Updated Description",
        permissions: [],
      };
      mockOnSubmit.mockResolvedValue(updatedRole);

      const { result } = renderHook(() =>
        useRoleForm({ role, onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setName("Updated Role");
        result.current.setDescription("Updated Description");
      });

      const permissionAssignments = [{ permission_id: 2, condition: null }];
      const removedPermissionIds = [1];

      let success = false;
      await act(async () => {
        success = await result.current.handleSubmit(
          permissionAssignments,
          removedPermissionIds,
        );
      });

      expect(success).toBe(true);
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: "Updated Role",
        description: "Updated Description",
        permissions: permissionAssignments,
        removed_permission_ids: removedPermissionIds,
      });
    });

    it("should not update name if role is locked", async () => {
      const role: Role = {
        id: 1,
        name: "Admin",
        description: "Admin Description",
        permissions: [],
        locked: true,
      };
      mockOnSubmit.mockResolvedValue(role);

      const { result } = renderHook(() =>
        useRoleForm({ role, onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setName("Changed Name");
        result.current.setDescription("Changed Description");
      });

      await act(async () => {
        await result.current.handleSubmit([], []);
      });

      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: undefined, // Name should be undefined for locked roles
        description: "Changed Description",
        permissions: undefined,
        removed_permission_ids: undefined,
      });
    });

    it("should handle empty permission assignments", async () => {
      const mockRole: Role = {
        id: 1,
        name: "New Role",
        description: "New Description",
        permissions: [],
      };
      mockOnSubmit.mockResolvedValue(mockRole);

      const { result } = renderHook(() =>
        useRoleForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setName("New Role");
      });

      await act(async () => {
        await result.current.handleSubmit([], []);
      });

      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: "New Role",
        description: null,
        permissions: undefined,
      });
    });

    it("should handle empty removed permission IDs", async () => {
      const role: Role = {
        id: 1,
        name: "Existing Role",
        description: "Existing Description",
        permissions: [],
      };
      mockOnSubmit.mockResolvedValue(role);

      const { result } = renderHook(() =>
        useRoleForm({ role, onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setName("Updated Role");
      });

      await act(async () => {
        await result.current.handleSubmit([], []);
      });

      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: "Updated Role",
        description: "Existing Description",
        permissions: undefined,
        removed_permission_ids: undefined,
      });
    });

    it("should handle submission error", async () => {
      const error = new Error("Submission failed");
      mockOnSubmit.mockRejectedValue(error);

      const { result } = renderHook(() =>
        useRoleForm({ onSubmit: mockOnSubmit, onError: mockOnError }),
      );

      act(() => {
        result.current.setName("Valid Name");
      });

      let success = true;
      await act(async () => {
        success = await result.current.handleSubmit([], []);
      });

      expect(success).toBe(false);
      expect(result.current.generalError).toBe("Submission failed");
      expect(mockOnError).toHaveBeenCalledWith("Submission failed");
      expect(result.current.isSubmitting).toBe(false);
    });

    it("should handle non-Error exception", async () => {
      mockOnSubmit.mockRejectedValue("String error");

      const { result } = renderHook(() =>
        useRoleForm({ onSubmit: mockOnSubmit, onError: mockOnError }),
      );

      act(() => {
        result.current.setName("Valid Name");
      });

      await act(async () => {
        await result.current.handleSubmit([], []);
      });

      expect(result.current.generalError).toBe("Failed to save role");
      expect(mockOnError).toHaveBeenCalledWith("Failed to save role");
    });

    it("should clear general error before submission", async () => {
      const mockRole: Role = {
        id: 1,
        name: "New Role",
        description: "New Description",
        permissions: [],
      };
      mockOnSubmit.mockResolvedValue(mockRole);

      const { result } = renderHook(() =>
        useRoleForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setGeneralError("Previous error");
        result.current.setName("Valid Name");
      });

      await act(async () => {
        await result.current.handleSubmit([], []);
      });

      expect(result.current.generalError).toBeNull();
    });

    it("should trim form data before submission", async () => {
      const mockRole: Role = {
        id: 1,
        name: "New Role",
        description: "New Description",
        permissions: [],
      };
      mockOnSubmit.mockResolvedValue(mockRole);

      const { result } = renderHook(() =>
        useRoleForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setName("  New Role  ");
        result.current.setDescription("  New Description  ");
      });

      await act(async () => {
        await result.current.handleSubmit([], []);
      });

      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: "New Role",
        description: "New Description",
        permissions: undefined,
      });
    });

    it("should set description to null if empty after trim", async () => {
      const mockRole: Role = {
        id: 1,
        name: "New Role",
        description: null,
        permissions: [],
      };
      mockOnSubmit.mockResolvedValue(mockRole);

      const { result } = renderHook(() =>
        useRoleForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setName("New Role");
        result.current.setDescription("   ");
      });

      await act(async () => {
        await result.current.handleSubmit([], []);
      });

      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: "New Role",
        description: null,
        permissions: undefined,
      });
    });
  });

  describe("reset", () => {
    it("should reset form to initial values", () => {
      const role: Role = {
        id: 1,
        name: "Initial Role",
        description: "Initial Description",
        permissions: [],
      };

      const { result } = renderHook(() => useRoleForm({ role }));

      act(() => {
        result.current.setName("Changed Name");
        result.current.setDescription("Changed Description");
        result.current.validate();
        result.current.setGeneralError("Test error");
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.formData).toEqual({
        name: "Initial Role",
        description: "Initial Description",
      });
      expect(result.current.errors).toEqual({});
      expect(result.current.generalError).toBeNull();
    });

    it("should reset to empty values in create mode", () => {
      const { result } = renderHook(() => useRoleForm({}));

      act(() => {
        result.current.setName("Test Name");
        result.current.setDescription("Test Description");
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.formData).toEqual({
        name: "",
        description: "",
      });
    });
  });
});
