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
import { TextArea } from "@/components/forms/TextArea";
import { TextInput } from "@/components/forms/TextInput";
import { useModal } from "@/hooks/useModal";
import { useShelfForm } from "@/hooks/useShelfForm";
import {
  deleteShelfCoverPicture,
  getShelfCoverPictureUrl,
  uploadShelfCoverPicture,
} from "@/services/shelfService";
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
    reset,
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

  const [coverFile, setCoverFile] = useState<File | null>(
    initialCoverFile || null,
  );
  const [coverError, setCoverError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isCoverDeleteStaged, setIsCoverDeleteStaged] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [coverPreviewUrl, setCoverPreviewUrl] = useState<string | null>(null);
  const hasUserTouchedCoverRef = useRef(false);

  // Create object URL for cover preview and clean up on unmount or file change
  useEffect(() => {
    if (coverFile && !isEditMode) {
      const objectUrl = URL.createObjectURL(coverFile);
      setCoverPreviewUrl(objectUrl);
      return () => {
        URL.revokeObjectURL(objectUrl);
      };
    }
    setCoverPreviewUrl(null);
    return () => {};
  }, [coverFile, isEditMode]);

  // Keep coverFile in sync with initialCoverFile for create mode,
  // but do not overwrite if the user has already interacted with the cover input.
  useEffect(() => {
    if (!isEditMode && initialCoverFile && !hasUserTouchedCoverRef.current) {
      setCoverFile((prev) => prev ?? initialCoverFile);
    }
  }, [initialCoverFile, isEditMode]);

  // Prevent body scroll when modal is open
  useModal(true);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  const handleOverlayKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  const handleModalClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
    },
    [],
  );

  const handleCancel = useCallback(() => {
    reset();
    setIsCoverDeleteStaged(false);
    setCoverFile(null);
    setCoverError(null);
    onClose();
  }, [reset, onClose]);

  const handleCoverFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        // Validate file type
        const validTypes = [
          "image/jpeg",
          "image/jpg",
          "image/png",
          "image/gif",
          "image/webp",
          "image/svg+xml",
        ];
        if (!validTypes.includes(file.type)) {
          setCoverError("Invalid file type. Please select an image file.");
          return;
        }
        // Validate file size (max 5MB)
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
          setCoverError("File size must be less than 5MB");
          return;
        }
        setCoverFile(file);
        setCoverError(null);
        hasUserTouchedCoverRef.current = true;
        // Clear staged deletion if a new file is selected
        setIsCoverDeleteStaged(false);
      }
    },
    [],
  );

  const handleClearCoverFile = useCallback(() => {
    setCoverFile(null);
    setCoverError(null);
    setIsCoverDeleteStaged(false);
    hasUserTouchedCoverRef.current = true;
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  const handleCoverDelete = useCallback(() => {
    // Stage the deletion - actual deletion happens on Save
    setIsCoverDeleteStaged(true);
    setCoverFile(null);
    setCoverError(null);
    hasUserTouchedCoverRef.current = true;
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  const handleFormSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      // Validate form first
      const isValid = await validateAndSubmit();
      if (!isValid) {
        return;
      }

      setIsSaving(true);
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
        if (savedShelf) {
          // Delete cover if deletion is staged
          if (isCoverDeleteStaged) {
            try {
              const updatedShelf = await deleteShelfCoverPicture(savedShelf.id);
              // Notify parent to refresh cover with updated shelf data
              onCoverDeleted?.(updatedShelf);
            } catch (error) {
              console.error("Failed to delete cover picture:", error);
              setCoverError(
                error instanceof Error
                  ? error.message
                  : "Failed to delete cover picture",
              );
              setIsSaving(false);
              return;
            }
          }

          // Upload cover picture if one was selected
          if (coverFile) {
            try {
              const updatedShelf = await uploadShelfCoverPicture(
                savedShelf.id,
                coverFile,
              );
              // Notify parent to refresh cover with updated shelf data
              onCoverSaved?.(updatedShelf);
            } catch (error) {
              console.error("Failed to upload cover picture:", error);
              setCoverError(
                error instanceof Error
                  ? error.message
                  : "Failed to upload cover picture",
              );
              setIsSaving(false);
              return;
            }
          }
        }

        onClose();
      } catch (error) {
        console.error("Failed to save shelf:", error);
        // Error handling is done by useShelfForm
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
      onCoverSaved,
      onCoverDeleted,
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

            <div className="space-y-4">
              <div className="font-medium text-sm text-text-a10">
                Cover picture (optional)
              </div>
              {isEditMode &&
              shelf &&
              shelf.cover_picture &&
              !isCoverDeleteStaged ? (
                <div className="space-y-4">
                  <img
                    src={getShelfCoverPictureUrl(shelf.id)}
                    alt={`${shelf.name} cover`}
                    className="h-32 w-32 rounded-lg object-cover"
                  />
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      size="medium"
                      onClick={handleCoverDelete}
                      disabled={isSaving}
                    >
                      Delete Cover
                    </Button>
                  </div>
                </div>
              ) : isEditMode && isCoverDeleteStaged ? (
                <div className="space-y-4">
                  <div className="flex h-32 w-32 items-center justify-center rounded-lg border-2 border-surface-a30 border-dashed bg-surface-a20">
                    <span className="text-sm text-text-a40">
                      Cover will be deleted
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      size="medium"
                      onClick={() => setIsCoverDeleteStaged(false)}
                      disabled={isSaving}
                    >
                      Cancel Delete
                    </Button>
                  </div>
                </div>
              ) : coverPreviewUrl ? (
                <div className="space-y-4">
                  <img
                    src={coverPreviewUrl}
                    alt="Cover preview"
                    className="h-32 w-32 rounded-lg object-cover"
                  />
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      size="medium"
                      onClick={handleClearCoverFile}
                      disabled={isSaving}
                    >
                      Clear
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml"
                    onChange={handleCoverFileChange}
                    className="block w-full rounded-lg border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] file:mr-4 file:cursor-pointer file:rounded file:border-0 file:bg-surface-a20 file:px-4 file:py-2 file:font-semibold file:text-sm file:text-text-a0 hover:file:bg-surface-a30 focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
                  />
                </div>
              )}
              {coverError && (
                <p
                  className="text-danger-a10 text-sm leading-normal"
                  role="alert"
                >
                  {coverError}
                </p>
              )}
            </div>

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
