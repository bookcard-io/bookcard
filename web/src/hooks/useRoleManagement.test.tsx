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

import { renderHook } from "@testing-library/react";
import type React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RolesContext } from "@/contexts/RolesContext";
import type { Role, RoleCreate, RoleUpdate } from "@/services/roleService";
import { useRoleManagement } from "./useRoleManagement";

describe("useRoleManagement", () => {
  let mockCreateRole: ReturnType<
    typeof vi.fn<(data: RoleCreate) => Promise<Role>>
  >;
  let mockUpdateRoleById: ReturnType<
    typeof vi.fn<(roleId: number, data: RoleUpdate) => Promise<Role>>
  >;
  let mockDeleteRoleById: ReturnType<
    typeof vi.fn<(roleId: number) => Promise<void>>
  >;
  let mockUpdateRole: ReturnType<typeof vi.fn<(role: Role) => void>>;

  const createWrapper = (
    contextValue: Partial<NonNullable<React.ContextType<typeof RolesContext>>>,
  ) => {
    return ({ children }: { children: React.ReactNode }) => {
      return (
        <RolesContext.Provider
          value={
            contextValue as unknown as React.ContextType<typeof RolesContext>
          }
        >
          {children}
        </RolesContext.Provider>
      );
    };
  };

  beforeEach(() => {
    mockCreateRole = vi.fn<(data: RoleCreate) => Promise<Role>>();
    mockUpdateRoleById = vi.fn<
      (roleId: number, data: RoleUpdate) => Promise<Role>
    >();
    mockDeleteRoleById = vi.fn<(roleId: number) => Promise<void>>();
    mockUpdateRole = vi.fn<(role: Role) => void>();
  });

  it("should return role management functions", () => {
    const wrapper = createWrapper({
      createRole: mockCreateRole,
      updateRoleById: mockUpdateRoleById,
      deleteRoleById: mockDeleteRoleById,
      updateRole: mockUpdateRole,
    });

    const { result } = renderHook(() => useRoleManagement(), { wrapper });

    expect(result.current).toHaveProperty("handleCreate");
    expect(result.current).toHaveProperty("handleUpdate");
    expect(result.current).toHaveProperty("handleDelete");
    expect(result.current).toHaveProperty("updateRoleOptimistic");
  });

  it("should call createRole from context when handleCreate is called", async () => {
    const mockRole: Role = {
      id: 1,
      name: "Test Role",
      description: "Test Description",
      permissions: [],
    };
    const roleCreate: RoleCreate = {
      name: "Test Role",
      description: "Test Description",
    };
    mockCreateRole.mockResolvedValue(mockRole);

    const wrapper = createWrapper({
      createRole: mockCreateRole,
      updateRoleById: mockUpdateRoleById,
      deleteRoleById: mockDeleteRoleById,
      updateRole: mockUpdateRole,
    });

    const { result } = renderHook(() => useRoleManagement(), { wrapper });

    const createdRole = await result.current.handleCreate(roleCreate);

    expect(mockCreateRole).toHaveBeenCalledWith(roleCreate);
    expect(createdRole).toEqual(mockRole);
  });

  it("should call updateRoleById from context when handleUpdate is called", async () => {
    const mockRole: Role = {
      id: 1,
      name: "Updated Role",
      description: "Updated Description",
      permissions: [],
    };
    const roleUpdate: RoleUpdate = {
      name: "Updated Role",
      description: "Updated Description",
    };
    mockUpdateRoleById.mockResolvedValue(mockRole);

    const wrapper = createWrapper({
      createRole: mockCreateRole,
      updateRoleById: mockUpdateRoleById,
      deleteRoleById: mockDeleteRoleById,
      updateRole: mockUpdateRole,
    });

    const { result } = renderHook(() => useRoleManagement(), { wrapper });

    const updatedRole = await result.current.handleUpdate(1, roleUpdate);

    expect(mockUpdateRoleById).toHaveBeenCalledWith(1, roleUpdate);
    expect(updatedRole).toEqual(mockRole);
  });

  it("should call deleteRoleById from context when handleDelete is called", async () => {
    mockDeleteRoleById.mockResolvedValue(undefined);

    const wrapper = createWrapper({
      createRole: mockCreateRole,
      updateRoleById: mockUpdateRoleById,
      deleteRoleById: mockDeleteRoleById,
      updateRole: mockUpdateRole,
    });

    const { result } = renderHook(() => useRoleManagement(), { wrapper });

    await result.current.handleDelete(1);

    expect(mockDeleteRoleById).toHaveBeenCalledWith(1);
  });

  it("should return updateRoleOptimistic from context", () => {
    const mockRole: Role = {
      id: 1,
      name: "Test Role",
      description: "Test Description",
      permissions: [],
    };

    const wrapper = createWrapper({
      createRole: mockCreateRole,
      updateRoleById: mockUpdateRoleById,
      deleteRoleById: mockDeleteRoleById,
      updateRole: mockUpdateRole,
    });

    const { result } = renderHook(() => useRoleManagement(), { wrapper });

    result.current.updateRoleOptimistic(mockRole);

    expect(mockUpdateRole).toHaveBeenCalledWith(mockRole);
  });
});
