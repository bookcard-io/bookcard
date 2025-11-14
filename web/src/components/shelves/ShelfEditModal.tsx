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
import { TextArea } from "@/components/forms/TextArea";
import { TextInput } from "@/components/forms/TextInput";
import { ShelfCoverSection } from "@/components/shelves/ShelfCoverSection";
import { useCoverFile } from "@/hooks/useCoverFile";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { useShelfCoverOperations } from "@/hooks/useShelfCoverOperations";
import { useShelfForm } from "@/hooks/useShelfForm";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";

export interface ShelfEditModalProps {
  /** Shelf to edit (null for create mode). */
  shelf: Shelf | null;
  /** Initial name for create mode (overrides shelf name if shelf is null). */
  initialName?: string;
  /** Initial cover file for create mode (e.g., from book cover). */
  initialCoverFile?: File | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when shelf is saved. Returns the created/updated shelf. */
  onSave: (data: ShelfCreate | ShelfUpdate) => Promise<Shelf>;
  /** Callback when cover picture is uploaded. Receives updated shelf with new cover. */
  onCoverSaved?: (shelf: Shelf) => void;
  /** Callback when cover picture is deleted. Receives updated shelf without cover. */
  onCoverDeleted?: (shelf: Shelf) => void;
}

/**
 * Shelf create/edit modal component.
 *
 * Displays a form for creating or editing a shelf in a modal overlay.
 * Follows SRP by delegating concerns to specialized hooks and components.
 * Follows IOC by accepting callbacks for all operations.
 * Follows DRY by reusing hooks and components.
 */
export function ShelfEditModal({
  shelf,
  initialName,
  initialCoverFile,
  onClose,
  onSave,
  onCoverSaved,
  onCoverDeleted,
}: ShelfEditModalProps) {
  const isEditMode = shelf !== null;
  const {
    name,
    description,
    isPublic,
    isSubmitting,
    errors,
    setName,
    setDescription,
    setIsPublic,
    handleSubmit: validateAndSubmit,
    reset: resetForm,
  } = useShelfForm({
    initialName: shelf?.name ?? initialName ?? "",
    initialDescription: shelf?.description ?? null,
    initialIsPublic: shelf?.is_public ?? false,
    onSubmit: async () => {
      // This won't be called since we handle submission manually
    },
    onError: (error) => {
      console.error("Shelf form error:", error);
    },
  });

  const {
    coverFile,
    coverPreviewUrl,
    coverError,
    isCoverDeleteStaged,
    fileInputRef,
    handleCoverFileChange,
    handleClearCoverFile,
    handleCoverDelete,
    handleCancelDelete,
    reset: resetCover,
  } = useCoverFile({
    initialCoverFile,
    isEditMode,
  });

  const [isSaving, setIsSaving] = useState(false);
  const [coverOperationError, setCoverOperationError] = useState<string | null>(
    null,
  );

  const { executeCoverOperations } = useShelfCoverOperations({
    onCoverSaved,
    onCoverDeleted,
    onError: (error) => {
      setCoverOperationError(error);
      console.error("Cover operation error:", error);
    },
  });

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

  const handleCoverFileChangeWithErrorClear = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setCoverOperationError(null);
      handleCoverFileChange(e);
    },
    [handleCoverFileChange],
  );

  const handleCancel = useCallback(() => {
    resetForm();
    resetCover();
    setCoverOperationError(null);
    onClose();
  }, [resetForm, resetCover, onClose]);

  const handleFormSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      // Validate form first
      const isValid = await validateAndSubmit();
      if (!isValid) {
        return;
      }

      setIsSaving(true);
      setCoverOperationError(null);

      try {
        // Prepare shelf data
        const data: ShelfCreate | ShelfUpdate = {
          name: name.trim(),
          description: description.trim() || null,
          is_public: isPublic,
        };

        // Save the shelf and get the result
        const savedShelf = await onSave(data);

        // Handle cover operations after shelf is saved
        if (savedShelf && (coverFile || isCoverDeleteStaged)) {
          await executeCoverOperations(
            savedShelf,
            coverFile,
            isCoverDeleteStaged,
          );
        }

        onClose();
      } catch (error) {
        console.error("Failed to save shelf:", error);
        // Error handling is done by useShelfForm and useShelfCoverOperations
      } finally {
        setIsSaving(false);
      }
    },
    [
      validateAndSubmit,
      name,
      description,
      isPublic,
      onSave,
      coverFile,
      isCoverDeleteStaged,
      executeCoverOperations,
      onClose,
    ],
  );

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="fixed inset-0 z-50 flex animate-[fadeIn_0.2s_ease-out] items-center justify-center overflow-y-auto bg-black/70 p-4"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className="relative w-full max-w-md animate-[slideUp_0.3s_ease-out] flex-col overflow-y-auto rounded-2xl bg-surface-a10 shadow-[var(--shadow-card-hover)]"
        role="dialog"
        aria-modal="true"
        aria-label={isEditMode ? "Edit shelf" : "Create shelf"}
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 z-10 flex h-10 w-10 items-center justify-center rounded-full border-none bg-transparent p-2 text-2xl text-text-a30 leading-none transition-colors duration-200 hover:bg-surface-a20 hover:text-text-a0 focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
          aria-label="Close"
        >
          ×
        </button>

        <div className="flex items-start justify-between gap-4 border-surface-a20 border-b pt-6 pr-16 pb-4 pl-6">
          <div className="flex min-w-0 flex-1 flex-col gap-1">
            <h2 className="m-0 truncate font-bold text-2xl text-text-a0 leading-[1.4]">
              {isEditMode ? "Edit shelf" : "Create shelf"}
            </h2>
          </div>
        </div>

        <form
          onSubmit={handleFormSubmit}
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 overflow-y-auto p-6">
            <TextInput
              label="Shelf name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              error={errors.name}
              required
              autoFocus
            />

            <TextArea
              label="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              error={errors.description}
              rows={4}
              placeholder="Optional description of the shelf"
            />

            <ShelfCoverSection
              shelf={shelf}
              isEditMode={isEditMode}
              isCoverDeleteStaged={isCoverDeleteStaged}
              coverPreviewUrl={coverPreviewUrl}
              coverError={coverError || coverOperationError}
              fileInputRef={fileInputRef}
              isSaving={isSaving}
              onCoverFileChange={handleCoverFileChangeWithErrorClear}
              onClearCoverFile={handleClearCoverFile}
              onCoverDelete={handleCoverDelete}
              onCancelDelete={handleCancelDelete}
            />

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isPublic"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <label
                htmlFor="isPublic"
                className="cursor-pointer text-base text-text-a0"
              >
                Share with everyone
              </label>
            </div>
          </div>

          <div className="flex flex-col gap-4 border-surface-a20 border-t bg-surface-tonal-a10 p-4 md:flex-row md:items-center md:justify-between md:gap-4 md:px-6 md:pt-4 md:pb-6">
            <div className="flex w-full flex-1 flex-col gap-2">
              {/* Error messages can go here if needed */}
            </div>
            <div className="flex w-full flex-shrink-0 flex-col-reverse justify-end gap-3 md:w-auto md:flex-row">
              <Button
                type="button"
                variant="ghost"
                size="medium"
                onClick={handleCancel}
                disabled={isSubmitting || isSaving}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="medium"
                loading={isSubmitting || isSaving}
              >
                {isEditMode ? "Save" : "Create"}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
