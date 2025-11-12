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

import { useCallback } from "react";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useModal } from "@/hooks/useModal";

export interface FullscreenImageModalProps {
  /** Image source URL. */
  src: string;
  /** Alternative text describing the image. */
  alt: string;
  /** Whether the modal is open. */
  isOpen: boolean;
  /** Called when the modal should be closed. */
  onClose: () => void;
}

/**
 * Fullscreen image modal.
 *
 * Displays an image in a fullscreen overlay and closes on click or Escape.
 * Single-responsibility: render and manage a fullscreen image dialog.
 */
export function FullscreenImageModal({
  src,
  alt,
  isOpen,
  onClose,
}: FullscreenImageModalProps) {
  useModal(isOpen);

  useKeyboardNavigation({
    onEscape: onClose,
    enabled: isOpen,
  });

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  if (!isOpen) {
    return null;
  }

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal pattern */
    <div
      className="fixed inset-0 z-[1000] flex cursor-zoom-out items-center justify-center bg-black/85"
      onClick={handleOverlayClick}
      role="presentation"
    >
      <div
        className="relative flex h-full w-full items-center justify-center outline-none"
        role="dialog"
        aria-modal="true"
        aria-label="Fullscreen image"
      >
        <button
          type="button"
          className="m-0 flex h-full w-full cursor-zoom-out items-center justify-center border-none bg-transparent p-0"
          aria-label="Close fullscreen image"
          onClick={onClose}
        >
          <span className="-m-px clip-[rect(0,0,0,0)] absolute h-px w-px overflow-hidden whitespace-nowrap border-0 p-0">
            Click anywhere to close
          </span>
          <ImageWithLoading
            src={src}
            alt={alt}
            fill={false}
            width={1600}
            height={1600}
            className="h-auto max-h-[95vh] w-auto max-w-[95vw] cursor-zoom-out rounded-md object-contain shadow-[0_8px_24px_rgba(0,0,0,0.5)]"
            unoptimized
          />
        </button>
      </div>
    </div>
  );
}
