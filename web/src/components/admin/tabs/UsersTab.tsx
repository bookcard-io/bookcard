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

"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/forms/Button";
import {
  createUser,
  deleteUser,
  type UserCreate,
  type UserUpdate,
  updateUser,
} from "@/services/userService";
import { DeleteUserConfirmationModal } from "../DeleteUserConfirmationModal";
import { UserEditModal } from "../UserEditModal";
import { type User, UsersTable } from "../UsersTable";

export function UsersTab() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    try {
      setIsLoading(true);

      const response = await fetch("/api/admin/users?limit=100&offset=0", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();
      setUsers(data);
    } catch (_err) {
      // Error handling can be enhanced here
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreateUser = useCallback(() => {
    setSelectedUser(null);
    setShowEditModal(true);
  }, []);

  const handleEditUser = useCallback((user: User) => {
    setSelectedUser(user);
    setShowEditModal(true);
  }, []);

  const handleDeleteUser = useCallback((user: User) => {
    setSelectedUser(user);
    setDeleteError(null);
    setShowDeleteModal(true);
  }, []);

  const handleSaveUser = useCallback(
    async (data: UserCreate | UserUpdate): Promise<User> => {
      let savedUser: User;
      if (selectedUser) {
        // Update existing user
        savedUser = await updateUser(selectedUser.id, data);
        // Update the user in the existing array
        setUsers((prevUsers) =>
          prevUsers.map((u) => (u.id === savedUser.id ? savedUser : u)),
        );
      } else {
        // Create new user - append to existing array
        savedUser = await createUser(data as UserCreate);
        setUsers((prevUsers) => [...prevUsers, savedUser]);
      }
      setShowEditModal(false);
      setSelectedUser(null);
      return savedUser;
    },
    [selectedUser],
  );

  const handleConfirmDelete = useCallback(async () => {
    if (!selectedUser) return;

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await deleteUser(selectedUser.id);
      // Remove the user from the existing array
      setUsers((prevUsers) =>
        prevUsers.filter((u) => u.id !== selectedUser.id),
      );
      setShowDeleteModal(false);
      setSelectedUser(null);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete user";
      setDeleteError(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  }, [selectedUser]);

  return (
    <>
      <div className="flex flex-col gap-6">
        <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold text-text-a0 text-xl">Users</h2>
            <Button
              type="button"
              variant="primary"
              size="xsmall"
              onClick={handleCreateUser}
            >
              <i className="pi pi-plus mr-2" aria-hidden="true" />
              Add user
            </Button>
          </div>
          <UsersTable
            users={users}
            isLoading={isLoading}
            onEdit={handleEditUser}
            onDelete={handleDeleteUser}
          />
        </div>
      </div>

      {showEditModal && (
        <UserEditModal
          user={selectedUser}
          onClose={() => {
            setShowEditModal(false);
            setSelectedUser(null);
          }}
          onSave={handleSaveUser}
        />
      )}

      {showDeleteModal && selectedUser && (
        <DeleteUserConfirmationModal
          isOpen={showDeleteModal}
          username={selectedUser.username}
          isDeleting={isDeleting}
          error={deleteError}
          onClose={() => {
            setShowDeleteModal(false);
            setSelectedUser(null);
            setDeleteError(null);
          }}
          onConfirm={handleConfirmDelete}
        />
      )}
    </>
  );
}
