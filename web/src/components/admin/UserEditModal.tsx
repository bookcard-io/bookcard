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

import { useCallback, useState } from "react";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { useRoleSuggestions } from "@/hooks/useRoleSuggestions";
import type { UserCreate, UserUpdate } from "@/services/userService";
import { RoleMultiInput } from "./RoleMultiInput";
import type { User } from "./UsersTable";

export interface UserEditModalProps {
  /** User to edit (null for create mode). */
  user?: User | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when user is saved. Returns the created/updated user. */
  onSave: (data: UserCreate | UserUpdate) => Promise<User>;
}

/**
 * User create/edit modal component.
 *
 * Displays a form for creating or editing a user in a modal overlay.
 * Follows SRP by delegating concerns to specialized hooks.
 * Follows IOC by accepting callbacks for all operations.
 *
 * Parameters
 * ----------
 * props : UserEditModalProps
 *     Component props including user, onClose, and onSave callbacks.
 */
export function UserEditModal({ user, onClose, onSave }: UserEditModalProps) {
  const isEditMode = user !== null && user !== undefined;

  // Form state
  const [username, setUsername] = useState(user?.username ?? "");
  const [fullName, setFullName] = useState(
    (user as { full_name?: string | null })?.full_name ?? "",
  );
  const [email, setEmail] = useState(user?.email ?? "");
  const [deviceEmail, setDeviceEmail] = useState(
    user?.default_ereader_email ?? "",
  );
  const [password, setPassword] = useState("");
  const [isAdmin, setIsAdmin] = useState(user?.is_admin ?? false);
  const [isActive, setIsActive] = useState(true);
  const [roleNames, setRoleNames] = useState<string[]>(
    user?.roles.map((r) => r.name) ?? [],
  );
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Get all roles from useRoleSuggestions hook (empty query = all roles)
  // This hook uses fetch deduplication, so multiple calls won't cause duplicate requests
  const { roles: allRoles } = useRoleSuggestions("", true);

  // Prevent body scroll when modal is open
  useModal(true);

  const { handleOverlayClick, handleModalClick } = useModalInteractions({
    onClose,
  });

  const handleOverlayKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  const validateForm = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};

    if (!username.trim()) {
      newErrors.username = "Username is required";
    } else if (username.length < 3) {
      newErrors.username = "Username must be at least 3 characters";
    } else if (username.length > 50) {
      newErrors.username = "Username must be at most 50 characters";
    }

    if (!email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Invalid email format";
    }

    if (!isEditMode && !password) {
      newErrors.password = "Password is required";
    } else if (password && password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [username, email, password, isEditMode]);

  const handleFormSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!validateForm()) {
        return;
      }

      setIsSaving(true);
      setGeneralError(null);

      try {
        // Convert role names to role IDs
        const roleIds = roleNames
          .map((name) => {
            const role = allRoles.find((r) => r.name === name);
            return role?.id;
          })
          .filter((id): id is number => id !== undefined);

        const data: UserCreate | UserUpdate = {
          username: username.trim(),
          full_name: fullName.trim() || null,
          email: email.trim(),
          ...(password ? { password } : {}),
          is_admin: isAdmin,
          is_active: isActive,
          role_ids: roleIds,
          default_device_email: deviceEmail.trim() || null,
        };

        await onSave(data);
        onClose();
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to save user";
        setGeneralError(errorMessage);
        console.error("Failed to save user:", error);
      } finally {
        setIsSaving(false);
      }
    },
    [
      username,
      fullName,
      email,
      deviceEmail,
      password,
      isAdmin,
      isActive,
      roleNames,
      allRoles,
      validateForm,
      onSave,
      onClose,
    ],
  );

  const handleCancel = useCallback(() => {
    setUsername(user?.username ?? "");
    setFullName((user as { full_name?: string | null })?.full_name ?? "");
    setEmail(user?.email ?? "");
    setDeviceEmail(user?.default_ereader_email ?? "");
    setPassword("");
    setIsAdmin(user?.is_admin ?? false);
    setIsActive(true);
    setRoleNames(user?.roles.map((r) => r.name) ?? []);
    setErrors({});
    setGeneralError(null);
    onClose();
  }, [user, onClose]);

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-50 modal-overlay-padding"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className="modal-container modal-container-shadow-default w-full max-w-2xl flex-col"
        role="dialog"
        aria-modal="true"
        aria-label={isEditMode ? "Edit user" : "Create user"}
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={onClose}
          className="modal-close-button modal-close-button-sm focus:outline"
          aria-label="Close"
        >
          <i className="pi pi-times" aria-hidden="true" />
        </button>

        <div className="flex items-start justify-between gap-4 border-surface-a20 border-b pt-6 pr-16 pb-4 pl-6">
          <div className="flex min-w-0 flex-1 flex-col gap-1">
            <h2 className="m-0 truncate font-bold text-2xl text-text-a0 leading-[1.4]">
              {isEditMode ? "Edit user" : "Create user"}
            </h2>
          </div>
        </div>

        <form
          onSubmit={handleFormSubmit}
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 overflow-y-auto p-6">
            {/* Row 1: Username and Full name */}
            <div className="grid grid-cols-2 gap-4">
              <TextInput
                id="username"
                label="Username"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  if (errors.username) {
                    setErrors((prev) => ({ ...prev, username: "" }));
                  }
                }}
                error={errors.username}
                required
                autoFocus
              />
              <TextInput
                id="fullName"
                label="Full name"
                value={fullName}
                onChange={(e) => {
                  setFullName(e.target.value);
                }}
              />
            </div>

            {/* Row 2: Email and Device email */}
            <div className="grid grid-cols-2 gap-4">
              <TextInput
                id="email"
                label="Email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) {
                    setErrors((prev) => ({ ...prev, email: "" }));
                  }
                }}
                error={errors.email}
                required
              />
              <TextInput
                id="deviceEmail"
                label="Device email (optional)"
                type="email"
                value={deviceEmail}
                onChange={(e) => {
                  setDeviceEmail(e.target.value);
                }}
                placeholder="device@example.com"
              />
            </div>

            {/* Row 3: Password and Roles */}
            <div className="grid grid-cols-2 gap-4">
              <TextInput
                id="password"
                label={
                  isEditMode
                    ? "New password (leave blank to keep current)"
                    : "Password"
                }
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) {
                    setErrors((prev) => ({ ...prev, password: "" }));
                  }
                }}
                error={errors.password}
                required={!isEditMode}
              />
              <RoleMultiInput
                id="roles"
                label="Roles"
                values={roleNames}
                onChange={setRoleNames}
                placeholder="Add roles..."
                helperText="Select roles to assign to this user"
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isAdmin"
                checked={isAdmin}
                onChange={(e) => setIsAdmin(e.target.checked)}
                className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <label
                htmlFor="isAdmin"
                className="cursor-pointer text-base text-text-a0"
              >
                Administrator
              </label>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isActive"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <label
                htmlFor="isActive"
                className="cursor-pointer text-base text-text-a0"
              >
                Active
              </label>
            </div>
          </div>

          <div className="modal-footer-between">
            <div className="flex w-full flex-1 flex-col gap-2">
              {generalError && (
                <p className="m-0 text-[var(--color-danger-a0)] text-sm">
                  {generalError}
                </p>
              )}
            </div>
            <div className="flex w-full flex-shrink-0 flex-col-reverse justify-end gap-3 md:w-auto md:flex-row">
              <Button
                type="button"
                variant="ghost"
                size="medium"
                onClick={handleCancel}
                disabled={isSaving}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="medium"
                loading={isSaving}
              >
                {isEditMode ? "Save changes" : "Create user"}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
