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

import { useEffect, useRef, useState } from "react";
import {
  deleteAuthorPhoto,
  uploadAuthorPhoto,
  uploadPhotoFromUrl,
} from "@/services/authorService";
import type { AuthorUpdate, AuthorWithMetadata } from "@/types/author";
import { PhotoChooserBar } from "./PhotoChooserBar";
import { PhotoThumbnailGrid } from "./PhotoThumbnailGrid";

interface PhotoTabProps {
  author: AuthorWithMetadata;
  form: AuthorUpdate;
  onFieldChange: <K extends keyof AuthorUpdate>(
    field: K,
    value: AuthorUpdate[K],
  ) => void;
}

/**
 * Component for the photo tab.
 *
 * Follows SRP by handling only photo-related fields.
 * Follows the moose project pattern with chooser bar and thumbnail grid.
 */
export function PhotoTab({ author, form, onFieldChange }: PhotoTabProps) {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [urlMode, setUrlMode] = useState(false);
  const [urlValue, setUrlValue] = useState("");
  const [thumbnails, setThumbnails] = useState<string[]>([]);
  const [selectedThumbnail, setSelectedThumbnail] = useState<string | null>(
    form.photo_url || author.photo_url || null,
  );
  // Track deleted photo URLs to prevent them from being re-added
  const [deletedPhotos, setDeletedPhotos] = useState<Set<string>>(new Set());

  // Initialize thumbnails with all known photos (user-uploaded + current)
  // Exclude deleted photos to prevent them from coming back
  useEffect(() => {
    const userPhotos = author.user_photos ?? [];
    const userPhotoUrls = userPhotos
      .map((p) => p.photo_url)
      .filter((url): url is string => Boolean(url))
      .filter((url) => !deletedPhotos.has(url)); // Exclude deleted photos

    const currentPhoto = form.photo_url || author.photo_url || null;
    // Don't include current photo if it's been deleted
    const validCurrentPhoto =
      currentPhoto && !deletedPhotos.has(currentPhoto) ? currentPhoto : null;

    const allUrlsSet = new Set<string>();
    userPhotoUrls.forEach((url) => {
      allUrlsSet.add(url);
    });
    if (validCurrentPhoto) {
      allUrlsSet.add(validCurrentPhoto);
    }

    if (allUrlsSet.size === 0) {
      setThumbnails([]);
      setSelectedThumbnail(null);
      return;
    }

    const allUrls = Array.from(allUrlsSet);
    setThumbnails(allUrls);

    // Prefer current form value, then primary user photo, then first available
    if (validCurrentPhoto) {
      setSelectedThumbnail(validCurrentPhoto);
      return;
    }

    const primaryUserPhoto = userPhotos.find(
      (p) => p.is_primary && p.photo_url && !deletedPhotos.has(p.photo_url),
    );
    if (primaryUserPhoto?.photo_url) {
      setSelectedThumbnail(primaryUserPhoto.photo_url);
      return;
    }

    setSelectedThumbnail(allUrls[0] ?? null);
  }, [author.user_photos, author.photo_url, form.photo_url, deletedPhotos]);

  useEffect(() => {
    if (!urlMode) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setUrlMode(false);
        setUrlValue("");
      }
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [urlMode]);

  const handleChoose = () => {
    fileRef.current?.click();
  };

  const handleUrlSubmit = async () => {
    if (!urlValue.trim() || !author.key) return;

    try {
      const result = await uploadPhotoFromUrl(author.key, urlValue.trim());
      // Add uploaded photo to thumbnails
      if (!thumbnails.includes(result.photo_url)) {
        setThumbnails([...thumbnails, result.photo_url]);
      }
      setSelectedThumbnail(result.photo_url);
      // Update form with photo URL
      onFieldChange("photo_url", result.photo_url);
      setUrlValue("");
      setUrlMode(false);
    } catch (error) {
      console.error("Failed to upload photo from URL:", error);
      // TODO: Show error toast/notification
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    const input = e.currentTarget;
    if (file && author.key) {
      try {
        const result = await uploadAuthorPhoto(author.key, file);
        // Add uploaded photo to thumbnails
        if (!thumbnails.includes(result.photo_url)) {
          setThumbnails([...thumbnails, result.photo_url]);
        }
        setSelectedThumbnail(result.photo_url);
        // Update form with photo URL
        onFieldChange("photo_url", result.photo_url);
      } catch (error) {
        console.error("Failed to upload photo:", error);
        // TODO: Show error toast/notification
      }
    }
    if (input) input.value = "";
  };

  const handleThumbnailSelect = (url: string) => {
    setSelectedThumbnail(url);
    onFieldChange("photo_url", url);
  };

  /**
   * Check if a photo URL is a user-uploaded photo.
   *
   * User-uploaded photos have URLs in the format: /api/authors/{author_id}/photos/{photo_id}
   *
   * Parameters
   * ----------
   * photoUrl : string
   *     Photo URL to check.
   *
   * Returns
   * -------
   * boolean
   *     True if the photo is user-uploaded, false otherwise.
   */
  const isUserUploadedPhoto = (photoUrl: string): boolean => {
    // Check if URL matches user-uploaded photo pattern
    return /\/api\/authors\/.*\/photos\/\d+$/.test(photoUrl);
  };

  /**
   * Extract photo ID from photo URL.
   *
   * Photo URLs are in the format: /api/authors/{author_id}/photos/{photo_id}
   *
   * Parameters
   * ----------
   * photoUrl : string
   *     Photo URL to extract ID from.
   *
   * Returns
   * -------
   * number | null
   *     Photo ID if found, null otherwise.
   */
  const extractPhotoId = (photoUrl: string): number | null => {
    const match = photoUrl.match(/\/photos\/(\d+)$/);
    return match?.[1] ? parseInt(match[1], 10) : null;
  };

  const handleDeletePhoto = async (url: string) => {
    if (!author.key) return;

    // Only delete user-uploaded photos
    if (!isUserUploadedPhoto(url)) {
      console.error("Cannot delete non-user-uploaded photo:", url);
      return;
    }

    const photoId = extractPhotoId(url);
    if (!photoId) {
      console.error("Could not extract photo ID from URL:", url);
      return;
    }

    try {
      await deleteAuthorPhoto(author.key, photoId);
      // Mark photo as deleted to prevent it from being re-added
      setDeletedPhotos((prev) => new Set(prev).add(url));
      // Remove from thumbnails
      setThumbnails((prev) =>
        prev.filter((thumbnailUrl) => thumbnailUrl !== url),
      );
      // If deleted photo was selected, clear selection or select another
      if (selectedThumbnail === url) {
        const remaining = thumbnails.filter(
          (thumbnailUrl) => thumbnailUrl !== url,
        );
        if (remaining.length > 0 && remaining[0]) {
          setSelectedThumbnail(remaining[0]);
          onFieldChange("photo_url", remaining[0]);
        } else {
          setSelectedThumbnail(null);
          onFieldChange("photo_url", null);
        }
      }
    } catch (error) {
      console.error("Failed to delete photo:", error);
      // TODO: Show error toast/notification
    }
  };

  return (
    <div className="flex h-full w-full flex-col">
      <PhotoChooserBar
        urlMode={urlMode}
        urlValue={urlValue}
        onUrlValueChange={setUrlValue}
        onUrlSubmit={handleUrlSubmit}
        onUrlCancel={() => {
          setUrlMode(false);
          setUrlValue("");
        }}
        onChooseFile={handleChoose}
        onEnterUrlMode={() => setUrlMode(true)}
      />
      <div
        className={`mt-4 flex rounded-lg border border-surface-a30 border-dashed ${
          thumbnails.length > 0
            ? "min-h-[220px] items-start justify-start overflow-y-auto p-3"
            : "h-[220px] items-center justify-center"
        }`}
      >
        {thumbnails.length > 0 ? (
          <PhotoThumbnailGrid
            thumbnails={thumbnails}
            selectedThumbnail={selectedThumbnail}
            onSelect={handleThumbnailSelect}
            onDelete={handleDeletePhoto}
            canDelete={isUserUploadedPhoto}
          />
        ) : (
          <button
            type="button"
            className="flex h-full w-full cursor-pointer items-center justify-center border-none bg-transparent text-text-a30 transition-colors hover:text-text-a0"
            onClick={handleChoose}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleChoose();
            }}
          >
            Upload an image
          </button>
        )}
      </div>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
}
