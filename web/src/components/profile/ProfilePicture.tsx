"use client";

import { useState } from "react";
import { useProfilePictureUpload } from "@/hooks/useProfilePictureUpload";
import { cn } from "@/libs/utils";

interface ProfilePictureProps {
  /**
   * URL of the profile picture, if available.
   */
  pictureUrl: string | null | undefined;
}

/**
 * Profile picture component with dropzone functionality.
 *
 * Displays user's profile picture or a placeholder icon.
 * Supports drag-and-drop and click-to-browse file upload.
 * Follows SRP by handling only profile picture display and upload UI.
 * Follows IOC by using useProfilePictureUpload hook for file handling.
 */
export function ProfilePicture({ pictureUrl }: ProfilePictureProps) {
  const {
    fileInputRef,
    isDragging,
    accept,
    dragHandlers,
    handleFileChange,
    handleClick,
    handleKeyDown,
  } = useProfilePictureUpload();
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="mx-auto flex-shrink-0 md:mx-0 md:w-[22%]">
      {/* biome-ignore lint/a11y/useSemanticElements: Div needed for drag-and-drop functionality */}
      <div
        className={cn(
          "relative flex aspect-square max-h-[300px] min-h-[200px] min-w-[200px] max-w-[300px] cursor-pointer items-center justify-center overflow-hidden rounded-full border border-surface-a20 bg-surface-tonal-a10 transition-colors duration-200",
          isDragging && "border-primary-a0 bg-surface-tonal-a20",
        )}
        {...dragHandlers}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        role="button"
        tabIndex={0}
        aria-label="Upload profile picture - click or drag and drop"
      >
        {pictureUrl ? (
          <img
            src={pictureUrl}
            alt="Profile"
            className="h-full w-full object-cover"
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
        {/* Browse button - inside circle, below icon - only visible on hover */}
        {(isHovered || isDragging) && (
          <div className="-translate-x-1/2 absolute bottom-8 left-1/2">
            <input
              ref={fileInputRef}
              type="file"
              accept={accept}
              onChange={handleFileChange}
              className="hidden"
              aria-label="Upload profile picture"
            />
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleClick();
              }}
              className="rounded border-0 bg-primary-a0 px-4 py-2 font-medium text-sm text-text-a0 transition-colors duration-200 hover:bg-primary-a10 focus:outline-none focus:ring-2 focus:ring-primary-a0 active:bg-primary-a20 disabled:cursor-not-allowed disabled:bg-surface-tonal-a20 disabled:text-text-a30"
            >
              Browse
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
