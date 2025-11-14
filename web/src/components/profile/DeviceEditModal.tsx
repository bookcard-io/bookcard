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

import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";
import { useModal } from "@/hooks/useModal";
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
 * Device create modal component.
 *
 * Displays a form for creating a new device in a modal overlay.
 * Follows SRP by delegating concerns to specialized hooks.
 * Follows IOC by accepting callbacks for all operations.
 * Follows DRY by reusing modal patterns from ShelfEditModal.
 */
export function DeviceEditModal({
  device,
  onClose,
  onSave,
}: DeviceEditModalProps) {
  const isEditMode = device !== null && device !== undefined;

  const [email, setEmail] = useState(device?.email || "");
  const [deviceName, setDeviceName] = useState(device?.device_name || "");
  const [deviceType, setDeviceType] = useState(device?.device_type || "kindle");
  const [preferredFormat, setPreferredFormat] = useState(
    device?.preferred_format || "",
  );
  const [isDefault, setIsDefault] = useState(device?.is_default || false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isShaking, setIsShaking] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [errors, setErrors] = useState<{
    email?: string;
    device_name?: string;
  }>({});

  // Track whether the initial fade-in animation has already played while
  // this modal instance is open. Using a ref avoids extra re-renders.
  const hasAnimatedRef = useRef(false);

  // Prevent body scroll when modal is open
  useModal(true);

  // After the first mount, mark the fade-in as done so subsequent re-renders
  // (e.g. validation errors, shake) don't replay the overlay fade animation.
  useEffect(() => {
    if (hasAnimatedRef.current) {
      return;
    }
    const timer = setTimeout(() => {
      hasAnimatedRef.current = true;
    }, 250); // Slightly longer than fadeIn duration (200ms)

    return () => clearTimeout(timer);
  }, []);

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
    const newErrors: { email?: string; device_name?: string } = {};

    if (!email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      newErrors.email = "Please enter a valid email address";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [email]);

  const handleFormSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!validateForm()) {
        return;
      }

      setIsSubmitting(true);
      setGeneralError(null);
      setErrors({});

      try {
        const data: DeviceCreate = {
          email: email.trim(),
          device_name: deviceName.trim() || null,
          device_type: deviceType,
          preferred_format: preferredFormat.trim() || null,
          is_default: isDefault,
        };

        await onSave(data);
        // Only close on success - if we reach here, save was successful
        onClose();
      } catch (error) {
        // Prevent modal from closing on error - catch all errors here
        // This ensures the modal stays open and displays the error
        console.error("Failed to save device:", error);

        // Trigger shake animation
        setIsShaking(true);
        setTimeout(() => {
          setIsShaking(false);
        }, 500);

        // Display error message
        if (error instanceof Error) {
          const errorMessage = error.message;
          // Translate technical error codes to user-friendly messages
          let displayMessage = errorMessage;
          if (errorMessage === "device_email_already_exists") {
            displayMessage = "A device with this email already exists.";
          }

          // Check if it's an email-related error
          if (
            errorMessage.includes("email") ||
            errorMessage.includes("device_email")
          ) {
            setErrors({ email: displayMessage });
          } else {
            setGeneralError(displayMessage);
          }
        } else {
          setGeneralError("Failed to save device. Please try again.");
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      email,
      deviceName,
      deviceType,
      preferredFormat,
      isDefault,
      validateForm,
      onSave,
      onClose,
    ],
  );

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-50 modal-overlay-padding"
      style={hasAnimatedRef.current ? { animation: "none" } : undefined}
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className={cn(
          "modal-container modal-container-shadow-default w-full max-w-md flex-col",
        )}
        style={
          hasAnimatedRef.current
            ? isShaking
              ? { animation: "shake 0.5s ease-in-out" }
              : { animation: "none" }
            : undefined
        }
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
              label="Email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                // Clear errors when user starts typing
                if (errors.email || generalError) {
                  setErrors({});
                  setGeneralError(null);
                }
              }}
              error={errors.email}
              required
              autoFocus
              placeholder="device@example.com"
            />

            <TextInput
              label="Device name"
              value={deviceName}
              onChange={(e) => setDeviceName(e.target.value)}
              error={errors.device_name}
              placeholder="e.g., My Kindle"
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
