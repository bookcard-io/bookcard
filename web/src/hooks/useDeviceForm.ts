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

import { useCallback, useState } from "react";
import type { DeviceCreate } from "@/components/profile/DeviceEditModal";
import type { EReaderDevice } from "@/components/profile/hooks/useUserProfile";
import { isEmailError, translateDeviceError } from "@/utils/deviceErrors";
import { validateEmail } from "@/utils/validation";

export interface UseDeviceFormOptions {
  /** Initial device data (for edit mode). */
  initialDevice?: EReaderDevice | null;
  /** Callback when form is successfully submitted. */
  onSubmit?: (data: DeviceCreate) => Promise<EReaderDevice> | Promise<void>;
  /** Callback when form submission fails. */
  onError?: (error: string) => void;
}

export interface UseDeviceFormReturn {
  /** Current email value. */
  email: string;
  /** Current device name value. */
  deviceName: string;
  /** Current device type value. */
  deviceType: string;
  /** Current preferred format value. */
  preferredFormat: string;
  /** Current is default value. */
  isDefault: boolean;
  /** Whether form is being submitted. */
  isSubmitting: boolean;
  /** Form validation errors. */
  errors: { email?: string; device_name?: string };
  /** General error message. */
  generalError: string | null;
  /** Update email value. */
  setEmail: (email: string) => void;
  /** Update device name value. */
  setDeviceName: (deviceName: string) => void;
  /** Update device type value. */
  setDeviceType: (deviceType: string) => void;
  /** Update preferred format value. */
  setPreferredFormat: (preferredFormat: string) => void;
  /** Update is default value. */
  setIsDefault: (isDefault: boolean) => void;
  /** Clear field errors when user starts typing. */
  clearErrors: () => void;
  /** Validate and submit the form. */
  handleSubmit: () => Promise<boolean>;
  /** Reset form to initial values. */
  reset: () => void;
}

/**
 * Hook for device create/edit form logic.
 *
 * Manages form state, validation, and submission for device creation and editing.
 * Follows SRP by separating form logic from UI components.
 * Follows DRY by centralizing form state management.
 * Follows IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseDeviceFormOptions
 *     Configuration options for the form.
 *
 * Returns
 * -------
 * UseDeviceFormReturn
 *     Object with form state and handlers.
 */
export function useDeviceForm(
  options: UseDeviceFormOptions = {},
): UseDeviceFormReturn {
  const { initialDevice, onSubmit, onError } = options;

  const [email, setEmail] = useState(initialDevice?.email || "");
  const [deviceName, setDeviceName] = useState(
    initialDevice?.device_name || "",
  );
  const [deviceType, setDeviceType] = useState(
    initialDevice?.device_type || "kindle",
  );
  const [preferredFormat, setPreferredFormat] = useState(
    initialDevice?.preferred_format || "",
  );
  const [isDefault, setIsDefault] = useState(
    initialDevice?.is_default || false,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{
    email?: string;
    device_name?: string;
  }>({});
  const [generalError, setGeneralError] = useState<string | null>(null);

  const validate = useCallback((): boolean => {
    const newErrors: { email?: string; device_name?: string } = {};

    const emailError = validateEmail(email);
    if (emailError) {
      newErrors.email = emailError;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [email]);

  const clearErrors = useCallback(() => {
    setErrors({});
    setGeneralError(null);
  }, []);

  const handleSubmit = useCallback(async (): Promise<boolean> => {
    if (!validate()) {
      return false;
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

      if (onSubmit) {
        await onSubmit(data);
      }

      return true;
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to save device. Please try again.";

      // Translate technical error codes to user-friendly messages
      const displayMessage = translateDeviceError(errorMessage);

      // Check if it's an email-related error
      if (isEmailError(errorMessage)) {
        setErrors({ email: displayMessage });
      } else {
        setGeneralError(displayMessage);
      }

      if (onError) {
        onError(displayMessage);
      }

      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [
    email,
    deviceName,
    deviceType,
    preferredFormat,
    isDefault,
    validate,
    onSubmit,
    onError,
  ]);

  const reset = useCallback(() => {
    setEmail(initialDevice?.email || "");
    setDeviceName(initialDevice?.device_name || "");
    setDeviceType(initialDevice?.device_type || "kindle");
    setPreferredFormat(initialDevice?.preferred_format || "");
    setIsDefault(initialDevice?.is_default || false);
    setErrors({});
    setGeneralError(null);
    setIsSubmitting(false);
  }, [initialDevice]);

  return {
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
    reset,
  };
}
