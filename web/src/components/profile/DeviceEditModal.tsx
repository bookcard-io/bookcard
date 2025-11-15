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

import { useCallback } from "react";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";
import { useUser } from "@/contexts/UserContext";
import { useDeviceForm } from "@/hooks/useDeviceForm";
import { useModal } from "@/hooks/useModal";
import { useModalAnimation } from "@/hooks/useModalAnimation";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { cn } from "@/libs/utils";
import type { EReaderDevice } from "./hooks/useUserProfile";

export interface DeviceCreate {
  email: string;
  device_name?: string | null;
  device_type?: string;
  preferred_format?: string | null;
  is_default?: boolean;
}

export interface DeviceEditModalProps {
  /** Device to edit (if provided, modal is in edit mode). */
  device?: EReaderDevice | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when device is saved. Returns the created/updated device. */
  onSave: (data: DeviceCreate) => Promise<EReaderDevice>;
}

/**
 * Device create/edit modal component.
 *
 * Displays a form for creating or editing a device in a modal overlay.
 * Follows SRP by delegating concerns to specialized hooks.
 * Follows SOC by separating form logic, validation, and animations.
 * Follows IOC by accepting callbacks for all operations.
 * Follows DRY by reusing modal patterns and form hooks.
 */
export function DeviceEditModal({
  device,
  onClose,
  onSave,
}: DeviceEditModalProps) {
  const isEditMode = device !== null && device !== undefined;
  const { user } = useUser();
  // Exclude current device from existing devices when editing
  const existingDevices =
    user?.ereader_devices?.filter((d) => d.id !== device?.id) || [];

  // Prevent body scroll when modal is open
  useModal(true);

  // Manage modal animations (fade-in and shake)
  const { overlayStyle, containerStyle, triggerShake } = useModalAnimation();

  // Manage form state, validation, and submission
  const {
    email,
    deviceName,
    deviceType,
    preferredFormat,
    isDefault,
    isSubmitting,
    errors,
    generalError,
    setEmail,
    setDeviceName,
    setDeviceType,
    setPreferredFormat,
    setIsDefault,
    clearErrors,
    handleSubmit,
  } = useDeviceForm({
    initialDevice: device,
    existingDevices,
    onSubmit: async (data) => {
      const result = await onSave(data);
      // Only close on success - if we reach here, save was successful
      onClose();
      return result;
    },
    onError: () => {
      // Trigger shake animation on error
      triggerShake();
    },
  });

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

  const handleFormSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      await handleSubmit();
    },
    [handleSubmit],
  );

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-50 modal-overlay-padding"
      style={overlayStyle}
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className={cn(
          "modal-container modal-container-shadow-default w-full max-w-md flex-col",
        )}
        style={containerStyle}
        role="dialog"
        aria-modal="true"
        aria-label={isEditMode ? "Edit device" : "Add device"}
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
              {isEditMode ? "Edit device" : "Add device"}
            </h2>
          </div>
        </div>

        <form
          onSubmit={handleFormSubmit}
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 overflow-y-auto p-6">
            <TextInput
              label="Device name"
              value={deviceName}
              onChange={(e) => setDeviceName(e.target.value)}
              error={errors.device_name}
              placeholder="e.g., My Kindle"
              autoFocus
            />

            <TextInput
              label="Email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                // Clear errors when user starts typing
                if (errors.email || generalError) {
                  clearErrors();
                }
              }}
              error={errors.email}
              required
              placeholder="device@example.com"
            />

            <div className="flex flex-col gap-2">
              <label
                htmlFor="deviceType"
                className="font-medium text-sm text-text-a0"
              >
                Device type
              </label>
              <select
                id="deviceType"
                value={deviceType}
                onChange={(e) => setDeviceType(e.target.value)}
                className="input-tonal px-3"
              >
                <option value="kindle">Kindle</option>
                <option value="kobo">Kobo</option>
                <option value="nook">Nook</option>
                <option value="generic">Generic</option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label
                htmlFor="preferredFormat"
                className="font-medium text-sm text-text-a0"
              >
                Preferred format (optional)
              </label>
              <select
                id="preferredFormat"
                value={preferredFormat}
                onChange={(e) => setPreferredFormat(e.target.value)}
                className="input-tonal px-3"
              >
                <option value="">None</option>
                <option value="epub">EPUB</option>
                <option value="mobi">MOBI</option>
                <option value="azw3">AZW3</option>
                <option value="pdf">PDF</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isDefault"
                checked={isDefault}
                onChange={(e) => setIsDefault(e.target.checked)}
                className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <label
                htmlFor="isDefault"
                className="cursor-pointer text-base text-text-a0"
              >
                Set as default device
              </label>
            </div>
          </div>

          <div className="flex flex-col gap-4 border-surface-a20 border-t bg-surface-tonal-a10 p-4 md:flex-row md:items-center md:justify-between md:gap-4 md:px-6 md:pt-4 md:pb-6">
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
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="medium"
                loading={isSubmitting}
              >
                {isEditMode ? "Save changes" : "Add device"}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
