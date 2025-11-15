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

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * Password change form component.
 *
 * Handles password change UI and validation.
 * Follows SRP by handling only password change UI.
 */
export function ChangePasswordForm() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const passwordsMatch = newPassword === confirmPassword;
  const isFormValid =
    currentPassword.length > 0 &&
    newPassword.length >= 8 &&
    confirmPassword.length >= 8 &&
    passwordsMatch;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!isFormValid) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch("/api/auth/password", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Failed to change password");
        setIsLoading(false);
        return;
      }

      // Password changed successfully - redirect to login with referrer
      // (logout is handled automatically by the API route)
      router.push("/login?referrer=password-change");
      router.refresh();
    } catch {
      setError("An error occurred. Please try again.");
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="rounded border-0 bg-primary-a0 px-4 py-2 font-medium text-sm text-text-a0 transition-colors duration-200 hover:bg-primary-a10 focus:outline-none focus:ring-2 focus:ring-primary-a0 active:bg-primary-a20 disabled:cursor-not-allowed disabled:bg-surface-tonal-a20 disabled:text-text-a30"
      >
        Change Password
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <label
          htmlFor="current-password"
          className="font-medium text-sm text-text-a20"
        >
          Current Password
        </label>
        <input
          id="current-password"
          type="password"
          value={currentPassword}
          onChange={(e) => {
            setCurrentPassword(e.target.value);
            if (error) {
              setError(null);
            }
          }}
          className="w-full rounded-md border border-surface-a20 bg-surface-tonal-a10 px-4 py-2.5 text-sm text-text-a0 transition-[border-color,background-color] duration-200 placeholder:text-text-a40 hover:border-surface-a30 focus:border-primary-a0 focus:bg-surface-tonal-a0 focus:outline-none"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label
          htmlFor="new-password"
          className="font-medium text-sm text-text-a20"
        >
          New Password
        </label>
        <input
          id="new-password"
          type="password"
          value={newPassword}
          onChange={(e) => {
            setNewPassword(e.target.value);
            if (error) {
              setError(null);
            }
          }}
          className="w-full rounded-md border border-surface-a20 bg-surface-tonal-a10 px-4 py-2.5 text-sm text-text-a0 transition-[border-color,background-color] duration-200 placeholder:text-text-a40 hover:border-surface-a30 focus:border-primary-a0 focus:bg-surface-tonal-a0 focus:outline-none"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label
          htmlFor="confirm-password"
          className="font-medium text-sm text-text-a20"
        >
          Confirm New Password
        </label>
        <input
          id="confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value);
            if (error) {
              setError(null);
            }
          }}
          className={`w-full rounded-md border px-4 py-2.5 text-sm text-text-a0 transition-[border-color,background-color] duration-200 placeholder:text-text-a40 hover:border-surface-a30 focus:bg-surface-tonal-a0 focus:outline-none ${
            confirmPassword.length > 0 && !passwordsMatch
              ? "border-error-a0 focus:border-error-a0"
              : "border-surface-a20 bg-surface-tonal-a10 focus:border-primary-a0"
          }`}
        />
        {confirmPassword.length > 0 && !passwordsMatch && (
          <p className="text-error-a0 text-xs">Passwords do not match</p>
        )}
      </div>

      {error && (
        <div className="rounded-md border border-error-a20 bg-error-a10 px-4 py-2.5 text-error-a0 text-sm">
          {error}
        </div>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={!isFormValid || isLoading}
          className="rounded border-0 bg-primary-a0 px-4 py-2 font-medium text-sm text-text-a0 transition-colors duration-200 hover:bg-primary-a10 focus:outline-none focus:ring-2 focus:ring-primary-a0 active:bg-primary-a20 disabled:cursor-not-allowed disabled:bg-surface-tonal-a20 disabled:text-text-a30"
        >
          {isLoading ? "Updating..." : "Update Password"}
        </button>
        <button
          type="button"
          onClick={() => {
            setIsOpen(false);
            setCurrentPassword("");
            setNewPassword("");
            setConfirmPassword("");
            setError(null);
          }}
          disabled={isLoading}
          className="rounded border border-surface-a20 bg-surface-tonal-a10 px-4 py-2 font-medium text-sm text-text-a0 transition-colors duration-200 hover:bg-surface-tonal-a20 focus:outline-none focus:ring-2 focus:ring-surface-a20 active:bg-surface-tonal-a30 disabled:cursor-not-allowed disabled:bg-surface-tonal-a20 disabled:text-text-a30"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
