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
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when shelf is saved. */
  onSave: (data: ShelfCreate | ShelfUpdate) => Promise<void>;
}

/**
 * Shelf create/edit modal component.
 *
 * Displays a form for creating or editing a shelf in a modal overlay.
 */
export function ShelfEditModal({
  shelf,
  onClose,
  onSave,
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
    handleSubmit,
    reset,
  } = useShelfForm({
    initialName: shelf?.name ?? "",
    initialDescription: shelf?.description ?? null,
    initialIsPublic: shelf?.is_public ?? false,
    onSubmit: onSave,
    onError: (error) => {
      console.error("Shelf form error:", error);
    },
  });

  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [isUploadingCover, setIsUploadingCover] = useState(false);
  const [coverError, setCoverError] = useState<string | null>(null);

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
      }
    },
    [],
  );

  const handleCoverUpload = useCallback(async () => {
    if (!coverFile || !shelf) return;

    setIsUploadingCover(true);
    setCoverError(null);

    try {
      await uploadShelfCoverPicture(shelf.id, coverFile);
      setCoverFile(null);
      // Refresh shelf data by closing and reopening or triggering a refresh
      onClose();
    } catch (error) {
      setCoverError(
        error instanceof Error
          ? error.message
          : "Failed to upload cover picture",
      );
    } finally {
      setIsUploadingCover(false);
    }
  }, [coverFile, shelf, onClose]);

  const handleCoverDelete = useCallback(async () => {
    if (!shelf) return;

    setIsUploadingCover(true);
    setCoverError(null);

    try {
      await deleteShelfCoverPicture(shelf.id);
      onClose();
    } catch (error) {
      setCoverError(
        error instanceof Error
          ? error.message
          : "Failed to delete cover picture",
      );
    } finally {
      setIsUploadingCover(false);
    }
  }, [shelf, onClose]);

  const handleFormSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const success = await handleSubmit();
      if (success) {
        // Upload cover picture if one was selected
        if (coverFile && shelf) {
          try {
            await uploadShelfCoverPicture(shelf.id, coverFile);
          } catch (error) {
            console.error("Failed to upload cover picture:", error);
          }
        }
        onClose();
      }
    },
    [handleSubmit, coverFile, shelf, onClose],
  );

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className="relative w-full max-w-md rounded-lg bg-bg-primary p-6 shadow-lg"
        role="dialog"
        aria-modal="true"
        aria-label={isEditMode ? "Edit Shelf" : "Create Shelf"}
        onMouseDown={handleModalClick}
      >
        <h2 className="mb-4 font-semibold text-xl">
          {isEditMode ? "Edit Shelf" : "Create Shelf"}
        </h2>

        <form onSubmit={handleFormSubmit} className="space-y-4">
          <TextInput
            label="Shelf Name"
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

          {isEditMode && shelf && (
            <div className="space-y-2">
              <div className="block font-medium text-sm">Cover Picture</div>
              {shelf.cover_picture ? (
                <div className="space-y-2">
                  <img
                    src={getShelfCoverPictureUrl(shelf.id)}
                    alt={`${shelf.name} cover`}
                    className="h-32 w-32 rounded object-cover"
                  />
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={handleCoverDelete}
                      disabled={isUploadingCover}
                    >
                      {isUploadingCover ? "Deleting..." : "Delete Cover"}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <input
                    type="file"
                    accept="image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml"
                    onChange={handleCoverFileChange}
                    className="block w-full text-gray-500 text-sm file:mr-4 file:rounded file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:font-semibold file:text-blue-700 file:text-sm hover:file:bg-blue-100"
                  />
                  {coverFile && (
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={handleCoverUpload}
                        disabled={isUploadingCover}
                      >
                        {isUploadingCover ? "Uploading..." : "Upload Cover"}
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => setCoverFile(null)}
                        disabled={isUploadingCover}
                      >
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>
              )}
              {coverError && (
                <p className="text-red-600 text-sm">{coverError}</p>
              )}
            </div>
          )}

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isPublic"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
            <label htmlFor="isPublic" className="text-sm">
              Share with everyone
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={handleCancel}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : isEditMode ? "Save" : "Create"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
