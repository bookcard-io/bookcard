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

import { useEffect, useState } from "react";
import { cn } from "@/libs/utils";

export interface ComicPageProps {
  bookId: number;
  format: string;
  pageNumber: number;
  onLoad?: () => void;
  className?: string;
}

/**
 * Comic page component.
 *
 * Fetches and displays a single comic page image.
 * Handles loading states and error display.
 * Follows SRP by focusing solely on page rendering.
 *
 * Parameters
 * ----------
 * props : ComicPageProps
 *     Component props including book ID, format, and page number.
 */
export function ComicPage({
  bookId,
  format,
  pageNumber,
  onLoad,
  className,
}: ComicPageProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!bookId || !format || !pageNumber) {
      return;
    }

    setIsLoading(true);
    setError(null);

    const params = new URLSearchParams({
      file_format: format,
    });

    const url = `/api/comic/${bookId}/pages/${pageNumber}?${params}`;
    setImageUrl(url);

    // Preload image
    const img = new Image();
    img.onload = () => {
      setIsLoading(false);
      onLoad?.();
    };
    img.onerror = () => {
      setIsLoading(false);
      setError("Failed to load page");
    };
    img.src = url;

    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [bookId, format, pageNumber, onLoad]);

  if (error) {
    return (
      <div className={cn("flex items-center justify-center", className)}>
        <span className="text-danger-a10">{error}</span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "relative flex h-full w-full items-center justify-center",
        className,
      )}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-surface-tonal-a0">
          <span className="text-text-a40">Loading...</span>
        </div>
      )}
      {imageUrl && (
        <img
          src={imageUrl}
          alt={`Page ${pageNumber}`}
          className={cn(
            "h-full w-full object-contain",
            isLoading && "opacity-0",
          )}
          onLoad={() => {
            setIsLoading(false);
            onLoad?.();
          }}
          onError={() => {
            setIsLoading(false);
            setError("Failed to load page");
          }}
        />
      )}
    </div>
  );
}
