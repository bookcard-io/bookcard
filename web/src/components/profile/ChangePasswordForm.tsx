"use client";

import { useState } from "react";

/**
 * Password change form component.
 *
 * Currently a no-op implementation as per requirements.
 * Follows SRP by handling only password change UI.
 */
export function ChangePasswordForm() {
  const [isOpen, setIsOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // No-op for now
    setIsOpen(false);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
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
          onChange={(e) => setCurrentPassword(e.target.value)}
          className="w-full rounded-lg border border-surface-a20 bg-surface-tonal-a10 px-4 py-2.5 text-sm text-text-a0 transition-[border-color,background-color] duration-200 placeholder:text-text-a40 hover:border-surface-a30 focus:border-primary-a0 focus:bg-surface-tonal-a0 focus:outline-none"
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
          onChange={(e) => setNewPassword(e.target.value)}
          className="w-full rounded-lg border border-surface-a20 bg-surface-tonal-a10 px-4 py-2.5 text-sm text-text-a0 transition-[border-color,background-color] duration-200 placeholder:text-text-a40 hover:border-surface-a30 focus:border-primary-a0 focus:bg-surface-tonal-a0 focus:outline-none"
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
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="w-full rounded-lg border border-surface-a20 bg-surface-tonal-a10 px-4 py-2.5 text-sm text-text-a0 transition-[border-color,background-color] duration-200 placeholder:text-text-a40 hover:border-surface-a30 focus:border-primary-a0 focus:bg-surface-tonal-a0 focus:outline-none"
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          className="rounded border-0 bg-primary-a0 px-4 py-2 font-medium text-sm text-text-a0 transition-colors duration-200 hover:bg-primary-a10 focus:outline-none focus:ring-2 focus:ring-primary-a0 active:bg-primary-a20 disabled:cursor-not-allowed disabled:bg-surface-tonal-a20 disabled:text-text-a30"
        >
          Update Password
        </button>
        <button
          type="button"
          onClick={() => {
            setIsOpen(false);
            setCurrentPassword("");
            setNewPassword("");
            setConfirmPassword("");
          }}
          className="rounded border border-surface-a20 bg-surface-tonal-a10 px-4 py-2 font-medium text-sm text-text-a0 transition-colors duration-200 hover:bg-surface-tonal-a20 focus:outline-none focus:ring-2 focus:ring-surface-a20 active:bg-surface-tonal-a30 disabled:cursor-not-allowed disabled:bg-surface-tonal-a20 disabled:text-text-a30"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
