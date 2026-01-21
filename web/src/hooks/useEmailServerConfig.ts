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

import { useCallback, useEffect, useState } from "react";
import type {
  EmailServerConfigData,
  EmailServerConfigUpdate,
} from "@/services/emailServerConfigService";
import {
  fetchEmailServerConfig,
  updateEmailServerConfig,
} from "@/services/emailServerConfigService";

const PASSWORD_PLACEHOLDER = "**********";

export interface EmailServerConfigFormData
  extends Partial<EmailServerConfigData> {
  smtp_password?: string;
}

export interface UseEmailServerConfigOptions {
  /** Callback when configuration is successfully saved. */
  onSaveSuccess?: (config: EmailServerConfigData) => void;
  /** Callback when an error occurs. */
  onError?: (error: string) => void;
}

export interface UseEmailServerConfigReturn {
  /** Current saved configuration. */
  config: EmailServerConfigData | null;
  /** Form data state. */
  formData: EmailServerConfigFormData;
  /** Whether configuration is loading. */
  isLoading: boolean;
  /** Whether configuration is saving. */
  isSaving: boolean;
  /** Error message, if any. */
  error: string | null;
  /** Whether form has unsaved changes. */
  hasChanges: boolean;
  /** Handler for field changes. */
  handleFieldChange: <K extends keyof EmailServerConfigFormData>(
    field: K,
    value: EmailServerConfigFormData[K],
  ) => void;
  /** Handler for server type changes. */
  handleServerTypeChange: (serverType: "smtp" | "gmail") => void;
  /** Handler for form submission. */
  handleSubmit: () => Promise<void>;
  /** Handler for cancel action. */
  handleCancel: () => void;
}

/**
 * Custom hook for managing email server configuration.
 *
 * Handles fetching, updating, and form state management for email server config.
 * Follows SRP by separating configuration logic from UI components.
 * Follows IOC by accepting callbacks as dependencies.
 * Follows DRY by centralizing form state and change tracking.
 *
 * Parameters
 * ----------
 * options : UseEmailServerConfigOptions
 *     Configuration options including callbacks.
 *
 * Returns
 * -------
 * UseEmailServerConfigReturn
 *     Object with configuration state and handlers.
 */
export function useEmailServerConfig(
  options: UseEmailServerConfigOptions = {},
): UseEmailServerConfigReturn {
  const { onSaveSuccess, onError } = options;

  const [config, setConfig] = useState<EmailServerConfigData | null>(null);
  const [formData, setFormData] = useState<EmailServerConfigFormData>({
    server_type: "smtp",
    smtp_host: null,
    smtp_port: 587,
    smtp_username: null,
    smtp_password: undefined,
    smtp_use_tls: true,
    smtp_use_ssl: false,
    smtp_from_email: null,
    smtp_from_name: null,
    max_email_size_mb: 25,
    gmail_token: null,
    enabled: true,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  /**
   * Initialize form data from configuration.
   */
  const initializeFormData = useCallback((data: EmailServerConfigData) => {
    setFormData({
      server_type: data.server_type || "smtp",
      smtp_host: data.smtp_host || null,
      smtp_port: data.smtp_port ?? 587,
      smtp_username: data.smtp_username || null,
      smtp_password: data.has_smtp_password ? PASSWORD_PLACEHOLDER : undefined,
      smtp_use_tls: data.smtp_use_tls ?? true,
      smtp_use_ssl: data.smtp_use_ssl ?? false,
      smtp_from_email: data.smtp_from_email || null,
      smtp_from_name: data.smtp_from_name || null,
      max_email_size_mb: data.max_email_size_mb ?? 25,
      gmail_token: data.gmail_token || null,
      enabled: data.enabled ?? true,
    });
  }, []);

  // Fetch current configuration
  useEffect(() => {
    const loadConfig = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchEmailServerConfig();
        setConfig(data);
        initializeFormData(data);
        setHasChanges(false);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load configuration";
        setError(message);
        if (onError) {
          onError(message);
        }
      } finally {
        setIsLoading(false);
      }
    };

    void loadConfig();
  }, [initializeFormData, onError]);

  // Track changes
  useEffect(() => {
    if (!config) return;

    const hasModifications =
      formData.server_type !== config.server_type ||
      formData.smtp_host !== (config.smtp_host || null) ||
      formData.smtp_port !== (config.smtp_port ?? 587) ||
      formData.smtp_username !== (config.smtp_username || null) ||
      formData.smtp_use_tls !== (config.smtp_use_tls ?? true) ||
      formData.smtp_use_ssl !== (config.smtp_use_ssl ?? false) ||
      formData.smtp_from_email !== (config.smtp_from_email || null) ||
      formData.smtp_from_name !== (config.smtp_from_name || null) ||
      formData.max_email_size_mb !== (config.max_email_size_mb ?? 25) ||
      formData.enabled !== (config.enabled ?? true) ||
      // Password change logic:
      // - If we have an existing password, any value other than the placeholder is a change
      // - If we don't have a password, any non-empty value is a change
      (() => {
        if (config.has_smtp_password) {
          return formData.smtp_password !== PASSWORD_PLACEHOLDER;
        }
        return !!formData.smtp_password;
      })();

    setHasChanges(hasModifications);
  }, [formData, config]);

  const handleFieldChange = useCallback(
    <K extends keyof EmailServerConfigFormData>(
      field: K,
      value: EmailServerConfigFormData[K],
    ) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
      setError(null);
    },
    [],
  );

  const handleServerTypeChange = useCallback(
    (serverType: "smtp" | "gmail") => {
      handleFieldChange("server_type", serverType);
    },
    [handleFieldChange],
  );

  const handleCancel = useCallback(() => {
    if (!config) return;
    initializeFormData(config);
    setError(null);
  }, [config, initializeFormData]);

  const handleSubmit = useCallback(async () => {
    try {
      setIsSaving(true);
      setError(null);

      const payload: EmailServerConfigUpdate = {
        server_type: formData.server_type || "smtp",
        enabled: formData.enabled ?? true,
        max_email_size_mb: formData.max_email_size_mb ?? 25,
      };

      // Add SMTP fields if SMTP is selected
      if (formData.server_type === "smtp") {
        if (formData.smtp_host) payload.smtp_host = formData.smtp_host;
        if (formData.smtp_port !== undefined)
          payload.smtp_port = formData.smtp_port;
        if (formData.smtp_username !== undefined)
          payload.smtp_username = formData.smtp_username || "";
        if (
          formData.smtp_password !== undefined &&
          formData.smtp_password !== PASSWORD_PLACEHOLDER
        ) {
          payload.smtp_password = formData.smtp_password;
        }
        if (formData.smtp_use_tls !== undefined) {
          payload.smtp_use_tls = formData.smtp_use_tls;
        }
        if (formData.smtp_use_ssl !== undefined) {
          payload.smtp_use_ssl = formData.smtp_use_ssl;
        }
        if (formData.smtp_from_email)
          payload.smtp_from_email = formData.smtp_from_email;
        if (formData.smtp_from_name)
          payload.smtp_from_name = formData.smtp_from_name;
      }

      // Add Gmail fields if Gmail is selected
      if (formData.server_type === "gmail") {
        if (formData.gmail_token) payload.gmail_token = formData.gmail_token;
      }

      const updatedConfig = await updateEmailServerConfig(payload);
      setConfig(updatedConfig);
      setFormData((prev) => ({
        ...prev,
        smtp_password: updatedConfig.has_smtp_password
          ? PASSWORD_PLACEHOLDER
          : undefined,
      }));
      setHasChanges(false);

      if (onSaveSuccess) {
        onSaveSuccess(updatedConfig);
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to save configuration";
      setError(message);
      if (onError) {
        onError(message);
      }
    } finally {
      setIsSaving(false);
    }
  }, [formData, onSaveSuccess, onError]);

  return {
    config,
    formData,
    isLoading,
    isSaving,
    error,
    hasChanges,
    handleFieldChange,
    handleServerTypeChange,
    handleSubmit,
    handleCancel,
  };
}
