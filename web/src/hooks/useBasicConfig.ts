import { useCallback, useEffect, useState } from "react";
import type {
  BasicConfig,
  BasicConfigUpdate,
} from "@/services/basicConfigService";
import {
  fetchBasicConfig,
  updateBasicConfig,
} from "@/services/basicConfigService";

export interface UseBasicConfigReturn {
  config: BasicConfig | null;
  formData: BasicConfig;
  isLoading: boolean;
  isSaving: boolean;
  hasChanges: boolean;
  error: string | null;
  handleFieldChange: <K extends keyof BasicConfig>(
    field: K,
    value: BasicConfig[K],
  ) => void;
  handleSubmit: () => Promise<void>;
  handleCancel: () => void;
}

const DEFAULT_FORM: BasicConfig = {
  allow_anonymous_browsing: false,
  allow_public_registration: false,
  require_email_for_registration: false,
  max_upload_size_mb: 100,
};

export function useBasicConfig(): UseBasicConfigReturn {
  const [config, setConfig] = useState<BasicConfig | null>(null);
  const [formData, setFormData] = useState<BasicConfig>(DEFAULT_FORM);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  const initializeForm = useCallback((data: BasicConfig) => {
    setFormData({
      allow_anonymous_browsing: data.allow_anonymous_browsing,
      allow_public_registration: data.allow_public_registration,
      require_email_for_registration: data.require_email_for_registration,
      max_upload_size_mb: data.max_upload_size_mb,
    });
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchBasicConfig();
        setConfig(data);
        initializeForm(data);
        setHasChanges(false);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load configuration";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, [initializeForm]);

  useEffect(() => {
    if (!config) return;
    const changed =
      formData.allow_anonymous_browsing !== config.allow_anonymous_browsing ||
      formData.allow_public_registration !== config.allow_public_registration ||
      formData.require_email_for_registration !==
        config.require_email_for_registration ||
      formData.max_upload_size_mb !== config.max_upload_size_mb;
    setHasChanges(changed);
  }, [config, formData]);

  const handleFieldChange = useCallback(
    <K extends keyof BasicConfig>(field: K, value: BasicConfig[K]) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
      setError(null);
    },
    [],
  );

  const handleSubmit = useCallback(async () => {
    try {
      setIsSaving(true);
      setError(null);
      const payload: BasicConfigUpdate = {
        allow_anonymous_browsing: formData.allow_anonymous_browsing,
        allow_public_registration: formData.allow_public_registration,
        require_email_for_registration: formData.require_email_for_registration,
        max_upload_size_mb: formData.max_upload_size_mb,
      };
      const updated = await updateBasicConfig(payload);
      setConfig(updated);
      initializeForm(updated);
      setHasChanges(false);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to save configuration";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  }, [formData, initializeForm]);

  const handleCancel = useCallback(() => {
    if (!config) return;
    initializeForm(config);
    setError(null);
  }, [config, initializeForm]);

  return {
    config,
    formData,
    isLoading,
    isSaving,
    hasChanges,
    error,
    handleFieldChange,
    handleSubmit,
    handleCancel,
  };
}
