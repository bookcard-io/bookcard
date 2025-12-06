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
import { cn } from "@/libs/utils";
import type { ComicAnnotation } from "../hooks/useComicAnnotations";

export interface ComicAnnotationLayerProps {
  annotations: ComicAnnotation[];
  pageNumber: number;
  imageWidth: number;
  imageHeight: number;
  containerWidth: number;
  containerHeight: number;
  onAnnotationClick?: (annotation: ComicAnnotation) => void;
  className?: string;
}

/**
 * Comic annotation layer component.
 *
 * Overlays annotations on top of comic pages.
 * Handles coordinate scaling from image dimensions to display dimensions.
 * Follows SRP by focusing solely on annotation rendering.
 *
 * Parameters
 * ----------
 * props : ComicAnnotationLayerProps
 *     Component props including annotations and dimensions.
 */
export function ComicAnnotationLayer({
  annotations,
  pageNumber,
  imageWidth,
  imageHeight,
  containerWidth,
  containerHeight,
  onAnnotationClick,
  className,
}: ComicAnnotationLayerProps) {
  // Filter annotations for this page
  const pageAnnotations = annotations.filter(
    (a) => a.page_number === pageNumber,
  );

  // Calculate scale factors
  const scaleX = containerWidth / imageWidth;
  const scaleY = containerHeight / imageHeight;

  const handleAnnotationClick = useCallback(
    (annotation: ComicAnnotation) => {
      onAnnotationClick?.(annotation);
    },
    [onAnnotationClick],
  );

  if (pageAnnotations.length === 0) {
    return null;
  }

  return (
    <div
      className={cn("pointer-events-none absolute inset-0", className)}
      style={{
        width: containerWidth,
        height: containerHeight,
      }}
    >
      {pageAnnotations.map((annotation) => {
        const x = annotation.x * scaleX;
        const y = annotation.y * scaleY;
        const width = annotation.width * scaleX;
        const height = annotation.height * scaleY;

        const colorClass =
          annotation.type === "highlight"
            ? "bg-yellow-400/30 border-yellow-400/50"
            : annotation.type === "bookmark"
              ? "bg-blue-400/30 border-blue-400/50"
              : "bg-green-400/30 border-green-400/50";

        return (
          <button
            key={annotation.id}
            type="button"
            className={cn(
              "pointer-events-auto absolute cursor-pointer border-2",
              colorClass,
            )}
            style={{
              left: `${x}px`,
              top: `${y}px`,
              width: `${width}px`,
              height: `${height}px`,
            }}
            onClick={() => handleAnnotationClick(annotation)}
            title={annotation.note || annotation.type}
          />
        );
      })}
    </div>
  );
}
