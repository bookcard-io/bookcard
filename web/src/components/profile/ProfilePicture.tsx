"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useUser } from "@/contexts/UserContext";
import { useProfilePictureDelete } from "@/hooks/useProfilePictureDelete";
import { useProfilePictureUpload } from "@/hooks/useProfilePictureUpload";
import { cn } from "@/libs/utils";
import { getProfilePictureUrlWithCacheBuster } from "@/utils/profile";

/**
 * Profile picture component with dropzone functionality.
 *
 * Displays user's profile picture or a placeholder icon.
 * Supports drag-and-drop and click-to-browse file upload.
 * Follows SRP by handling only profile picture display and upload UI.
 * Follows IOC by using hooks for file handling operations.
 */
export function ProfilePicture() {
  const { user, refresh } = useUser();
  const [error, setError] = useState<string | null>(null);
  const [pictureCacheBuster, setPictureCacheBuster] = useState(Date.now());
  const previousPicturePathRef = useRef<string | null>(null);

  // Track when profile picture path actually changes
  useEffect(() => {
    const currentPath = user?.profile_picture ?? null;
    const previousPath = previousPicturePathRef.current;

    // Only update cache buster if the profile picture path actually changed
    if (currentPath !== previousPath) {
      setPictureCacheBuster(Date.now());
      previousPicturePathRef.current = currentPath;
    }
  }, [user?.profile_picture]);

  const handleUploadSuccess = useCallback(async () => {
    setError(null);
    // Update cache buster when upload succeeds
    setPictureCacheBuster(Date.now());
    await refresh();
  }, [refresh]);

  const handleUploadError = useCallback((errorMessage: string) => {
    setError(errorMessage);
  }, []);

  const handleDeleteSuccess = useCallback(async () => {
    setError(null);
    // Update cache buster when delete succeeds
    setPictureCacheBuster(Date.now());
    await refresh();
  }, [refresh]);

  const handleDeleteError = useCallback((errorMessage: string) => {
    setError(errorMessage);
  }, []);

  const {
    fileInputRef,
    isDragging,
    accept,
    dragHandlers,
    handleFileChange,
    handleClick,
    handleKeyDown,
    isUploading,
  } = useProfilePictureUpload({
    onUploadSuccess: handleUploadSuccess,
    onUploadError: handleUploadError,
  });

  const { isDeleting, deleteProfilePicture } = useProfilePictureDelete({
    onDeleteSuccess: handleDeleteSuccess,
    onDeleteError: handleDeleteError,
  });

  // Generate profile picture URL with cache-busting
  // Only updates when profile picture path actually changes
  const profilePictureUrl = useMemo(() => {
    if (!user?.profile_picture) {
      return null;
    }
    return getProfilePictureUrlWithCacheBuster(pictureCacheBuster);
  }, [user?.profile_picture, pictureCacheBuster]);

  return (
    <div className="relative mx-auto max-w-[300px] flex-shrink-0 md:mx-0 md:w-[22%]">
      {/* biome-ignore lint/a11y/useSemanticElements: Div needed for drag-and-drop functionality */}
      <div
        className={cn(
          "relative flex aspect-square max-h-[300px] min-h-[120px] min-w-[120px] max-w-[300px] cursor-pointer items-center justify-center overflow-hidden rounded-full border border-surface-a20 bg-surface-tonal-a10 transition-colors duration-200",
          isDragging && "border-primary-a0 bg-surface-tonal-a20",
        )}
        {...dragHandlers}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-label="Upload profile picture - click or drag and drop"
      >
        {/* File input - always in DOM for ref to work, even when dialog is open */}
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileChange}
          className="hidden"
          aria-label="Upload profile picture"
          disabled={isUploading || isDeleting}
        />
        {profilePictureUrl ? (
          <img
            src={profilePictureUrl}
            alt="Profile"
            className="h-full w-full object-cover"
            key={profilePictureUrl}
          />
        ) : (
          <div className="relative flex h-full w-full items-center justify-center">
            {/* Muted, blurred circular background */}
            <div className="absolute inset-0 rounded-full bg-surface-tonal-a20 opacity-50 blur-xl" />
            {/* Icon - dead centered */}
            <i
              className="pi pi-user relative text-7xl text-text-a30"
              aria-hidden="true"
            />
          </div>
        )}
        {error && (
          <div className="-translate-x-1/2 absolute bottom-2 left-1/2 rounded bg-[var(--color-danger-a0)] px-3 py-1 text-text-a0 text-xs">
            {error}
          </div>
        )}
      </div>
      {/* Action buttons - below circle, always visible, centered */}
      <div className="mt-4 flex justify-center gap-2">
        {user?.profile_picture && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              void deleteProfilePicture();
            }}
            disabled={isUploading || isDeleting}
            className="rounded border-0 bg-[var(--color-danger-a-1)] px-4 py-2 font-medium text-sm text-text-a0 transition-colors duration-200 hover:bg-[var(--color-danger-a0)] hover:text-text-a0 focus:outline-none focus:ring-2 focus:ring-[var(--color-danger-a-1)] active:bg-[var(--color-danger-a-1)] disabled:cursor-not-allowed disabled:bg-surface-tonal-a20 disabled:text-text-a30"
            aria-label="Delete profile picture"
          >
            {isDeleting ? (
              <i className="pi pi-spin pi-spinner" aria-hidden="true" />
            ) : (
              "Delete"
            )}
          </button>
        )}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            handleClick();
          }}
          disabled={isUploading || isDeleting}
          className="rounded border-0 bg-surface-a20 px-4 py-2 font-medium text-sm text-text-a0 transition-colors duration-200 hover:bg-surface-a30 focus:outline-none focus:ring-2 focus:ring-primary-a0 active:bg-primary-a20 disabled:cursor-not-allowed disabled:bg-surface-tonal-a20 disabled:text-text-a30"
        >
          {isUploading ? "Uploading..." : "Browse"}
        </button>
      </div>
    </div>
  );
}
