import { useEffect, useRef } from "react";
import { useBlurAfterClick } from "@/components/profile/BlurAfterClickContext";
import { useBasicConfig } from "@/hooks/useBasicConfig";

export function SystemSettingsConfig() {
  const {
    formData,
    config,
    isLoading,
    error,
    handleFieldChange,
    handleSubmit,
  } = useBasicConfig();
  const { onBlurChange } = useBlurAfterClick();
  const isInitialLoadRef = useRef(true);
  const previousAnonymousBrowsingRef = useRef<boolean | null>(null);
  const previousPublicRegistrationRef = useRef<boolean | null>(null);
  const previousRequireEmailRef = useRef<boolean | null>(null);
  const previousMaxUploadSizeRef = useRef<number | null>(null);

  // Track when initial load completes
  useEffect(() => {
    if (!isLoading && config) {
      isInitialLoadRef.current = false;
      previousAnonymousBrowsingRef.current = config.allow_anonymous_browsing;
      previousPublicRegistrationRef.current = config.allow_public_registration;
      previousRequireEmailRef.current = config.require_email_for_registration;
      previousMaxUploadSizeRef.current = config.max_upload_size_mb;
    }
  }, [isLoading, config]);

  // Auto-save when allow_anonymous_browsing changes
  useEffect(() => {
    if (
      isInitialLoadRef.current ||
      isLoading ||
      !config ||
      previousAnonymousBrowsingRef.current === null
    ) {
      return;
    }

    if (
      formData.allow_anonymous_browsing !== previousAnonymousBrowsingRef.current
    ) {
      previousAnonymousBrowsingRef.current = formData.allow_anonymous_browsing;
      void handleSubmit();
    }
  }, [formData.allow_anonymous_browsing, config, isLoading, handleSubmit]);

  // Auto-save when allow_public_registration changes
  useEffect(() => {
    if (
      isInitialLoadRef.current ||
      isLoading ||
      !config ||
      previousPublicRegistrationRef.current === null
    ) {
      return;
    }

    if (
      formData.allow_public_registration !==
      previousPublicRegistrationRef.current
    ) {
      previousPublicRegistrationRef.current =
        formData.allow_public_registration;
      void handleSubmit();
    }
  }, [formData.allow_public_registration, config, isLoading, handleSubmit]);

  // Auto-save when require_email_for_registration changes
  useEffect(() => {
    if (
      isInitialLoadRef.current ||
      isLoading ||
      !config ||
      previousRequireEmailRef.current === null
    ) {
      return;
    }

    if (
      formData.require_email_for_registration !==
      previousRequireEmailRef.current
    ) {
      previousRequireEmailRef.current = formData.require_email_for_registration;
      void handleSubmit();
    }
  }, [
    formData.require_email_for_registration,
    config,
    isLoading,
    handleSubmit,
  ]);

  // Auto-save when max_upload_size_mb changes
  useEffect(() => {
    if (
      isInitialLoadRef.current ||
      isLoading ||
      !config ||
      previousMaxUploadSizeRef.current === null
    ) {
      return;
    }

    if (formData.max_upload_size_mb !== previousMaxUploadSizeRef.current) {
      previousMaxUploadSizeRef.current = formData.max_upload_size_mb;
      void handleSubmit();
    }
  }, [formData.max_upload_size_mb, config, isLoading, handleSubmit]);

  return (
    <div className="flex flex-col gap-4">
      {error && (
        <div className="rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
          <input
            type="checkbox"
            checked={formData.allow_anonymous_browsing}
            onChange={onBlurChange((e) => {
              handleFieldChange("allow_anonymous_browsing", e.target.checked);
            })}
            className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
            disabled={isLoading}
          />
          <div className="flex flex-col gap-1">
            <span className="font-medium text-sm text-text-a10">
              Allow Anonymous Browsing
            </span>
            <span className="text-text-a30 text-xs">
              Enables viewing, downloading, and reading without login. Write
              operations remain restricted to authenticated users.
            </span>
          </div>
        </label>

        <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
          <input
            type="checkbox"
            checked={formData.allow_public_registration}
            onChange={onBlurChange((e) => {
              handleFieldChange("allow_public_registration", e.target.checked);
            })}
            className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
            disabled={isLoading}
          />
          <div className="flex flex-col gap-1">
            <span className="font-medium text-sm text-text-a10">
              Allow Public Registration
            </span>
            <span className="text-text-a30 text-xs">
              Enables users to create accounts without an invitation. When
              disabled, only invited users can register.
            </span>
          </div>
        </label>

        <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
          <input
            type="checkbox"
            checked={formData.require_email_for_registration}
            onChange={onBlurChange((e) => {
              handleFieldChange(
                "require_email_for_registration",
                e.target.checked,
              );
            })}
            className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
            disabled={isLoading}
          />
          <div className="flex flex-col gap-1">
            <span className="font-medium text-sm text-text-a10">
              Require Email for Registration
            </span>
            <span className="text-text-a30 text-xs">
              When enabled, users must provide a valid email address during
              registration. Email verification may be required.
            </span>
          </div>
        </label>

        <div className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
          <div className="mt-0.5 h-4 w-4" />
          <div className="flex flex-1 flex-col gap-1">
            <label
              htmlFor="max_upload_size_mb"
              className="font-medium text-sm text-text-a10"
            >
              Maximum Upload Size (MB)
            </label>
            <span className="mb-2 text-text-a30 text-xs">
              Maximum file size allowed for uploads in megabytes. Files larger
              than this limit will be rejected.
            </span>
            <div className="flex items-center gap-2">
              <input
                id="max_upload_size_mb"
                type="number"
                min="1"
                step="1"
                className="w-24 rounded-md border border-surface-a20 bg-surface-a0 px-3 py-2 text-sm text-text-a0 focus:border-primary-a0 focus:outline-none focus:ring-2 focus:ring-primary-a0"
                value={formData.max_upload_size_mb}
                onChange={(e) => {
                  const value = parseInt(e.target.value, 10);
                  if (!Number.isNaN(value) && value > 0) {
                    handleFieldChange("max_upload_size_mb", value);
                  }
                }}
                onBlur={() => {
                  if (!isInitialLoadRef.current && config) {
                    void handleSubmit();
                  }
                }}
                disabled={isLoading}
              />
              <span className="text-sm text-text-a40">MB</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
