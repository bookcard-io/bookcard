"use client";

import { useState } from "react";
import { CgToggleOff, CgToggleOn } from "react-icons/cg";
import { FaCheckCircle, FaExclamationCircle, FaSpinner } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { cn } from "@/libs/utils";
import {
  type DownloadClient,
  type DownloadClientCreate,
  type DownloadClientTestResponse,
  DownloadClientType,
  type DownloadClientUpdate,
} from "@/types/downloadClient";
import { renderModalPortal } from "@/utils/modal";
import {
  DownloadClientConfigProvider,
  useDownloadClientConfig,
} from "./DownloadClientConfigContext";
import { FieldGroup } from "./DownloadClientFields";
import { useConnectionTest } from "./useConnectionTest";
import { useDownloadClientForm } from "./useDownloadClientForm";

interface DownloadClientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: DownloadClientCreate | DownloadClientUpdate) => Promise<void>;
  initialData?: DownloadClient;
  testConnection: (id: number) => Promise<DownloadClientTestResponse>;
  testNewConnection: (
    data: DownloadClientCreate,
  ) => Promise<DownloadClientTestResponse>;
}

function DownloadClientModalContent({
  onClose,
  onSave,
  initialData,
  testConnection,
  testNewConnection,
}: Omit<DownloadClientModalProps, "isOpen">) {
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  const isEditMode = !!initialData;
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { configs } = useDownloadClientConfig();
  const { formData, handleChange, getPayload } =
    useDownloadClientForm(initialData);

  const { isTesting, testResult, handleTest } = useConnectionTest({
    testConnection,
    testNewConnection,
    initialData,
    getPayload,
  });

  const currentConfig = configs[formData.client_type];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = getPayload();

      // Handle empty password/username if editing
      if (isEditMode) {
        if (!payload.password) delete payload.password;
        if (!payload.username) delete payload.username;
      }

      await onSave(payload);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1002 modal-overlay-padding"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className={cn(
          "modal-container modal-container-shadow-default w-full max-w-2xl flex-col",
          "max-h-[90vh] overflow-hidden",
        )}
        role="dialog"
        aria-modal="true"
        aria-label={isEditMode ? "Edit Download Client" : "Add Download Client"}
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
          <h2 className="m-0 truncate font-bold text-2xl text-text-a0 leading-[1.4]">
            {isEditMode ? "Edit Download Client" : "Add Download Client"}
          </h2>
        </div>

        <form
          onSubmit={handleSubmit}
          className={cn("flex min-h-0 flex-1 flex-col overflow-hidden")}
        >
          <div
            className={cn(
              "flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto p-6",
            )}
          >
            <TextInput
              id="name"
              label="Name"
              value={formData.name || ""}
              onChange={(e) => handleChange("name", e.target.value)}
              placeholder={`e.g. ${formData.client_type} (Optional)`}
              autoFocus
            />

            <div className="flex flex-col gap-1">
              <label
                htmlFor="client_type"
                className="font-medium text-sm text-text-a20"
              >
                Client Type
              </label>
              <select
                id="client_type"
                value={formData.client_type}
                onChange={(e) =>
                  handleChange(
                    "client_type",
                    e.target.value as DownloadClientType,
                  )
                }
                disabled={isEditMode}
                className={cn(
                  "rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a0)] px-3 py-2 text-text-a0 focus:border-[var(--color-primary-a0)] focus:outline-none",
                  isEditMode && "cursor-not-allowed opacity-50",
                )}
              >
                {Object.values(DownloadClientType).map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            {/* Basic Fields */}
            <FieldGroup
              fields={currentConfig.fields}
              formData={formData}
              onChange={handleChange}
              isEditMode={isEditMode}
              requiredFields={["host", "port"]}
            />

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="enabled"
                checked={formData.enabled}
                onChange={(e) => handleChange("enabled", e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-[var(--color-primary-a0)] focus:ring-[var(--color-primary-a0)]"
              />
              <label htmlFor="enabled" className="text-sm text-text-a0">
                Enabled
              </label>
            </div>

            {/* Advanced Settings Toggle */}
            {currentConfig.advancedFields &&
              currentConfig.advancedFields.length > 0 && (
                <div className="flex flex-col gap-4">
                  <button
                    type="button"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="flex w-fit items-center gap-2 text-sm text-text-a0"
                  >
                    {showAdvanced ? (
                      <CgToggleOff className="h-5 w-5 text-[var(--color-primary-a0)]" />
                    ) : (
                      <CgToggleOn className="h-5 w-5" />
                    )}
                    <span>Advanced Settings</span>
                  </button>

                  {showAdvanced && (
                    <FieldGroup
                      fields={currentConfig.advancedFields}
                      formData={formData}
                      onChange={handleChange}
                      isEditMode={isEditMode}
                    />
                  )}
                </div>
              )}
          </div>

          <div className="modal-footer-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="secondary"
                size="medium"
                onClick={handleTest}
                disabled={isTesting || isSubmitting}
              >
                {isTesting ? <FaSpinner className="mr-2 animate-spin" /> : null}
                Test
              </Button>
              {testResult && (
                <div
                  className={cn(
                    "flex items-center gap-2 text-sm",
                    testResult.success
                      ? "text-[var(--color-success-a0)]"
                      : "text-[var(--color-danger-a0)]",
                  )}
                >
                  {testResult.success ? (
                    <FaCheckCircle className="h-4 w-4" />
                  ) : (
                    <FaExclamationCircle className="h-4 w-4" />
                  )}
                  {testResult.message}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
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
                Save
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export function DownloadClientModal(props: DownloadClientModalProps) {
  useModal(props.isOpen);

  if (!props.isOpen) {
    return null;
  }

  return renderModalPortal(
    <DownloadClientConfigProvider>
      <DownloadClientModalContent {...props} />
    </DownloadClientConfigProvider>,
  );
}
