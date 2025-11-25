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

import Image, { type ImageProps } from "next/image";
import { useEffect, useRef, useState } from "react";

/**
 * Props for ImageWithLoading component.
 *
 * Extends Next.js Image props to maintain full compatibility.
 */
export interface ImageWithLoadingProps extends ImageProps {
  /** Optional className for the container. */
  containerClassName?: string;
  /** Optional external loading state (e.g., for backend processing). If provided, overrides internal image loading state. */
  isLoading?: boolean;
}

/**
 * Image component with loading curtain overlay.
 *
 * Displays a loading spinner overlay while the image is loading.
 * The overlay eases out smoothly once the image has loaded.
 * Follows SRP by focusing solely on image loading state management.
 *
 * @param props - Next.js Image props plus optional container className.
 * @returns Image component with loading indicator.
 */
export function ImageWithLoading({
  containerClassName,
  className,
  onLoad,
  isLoading: externalIsLoading,
  ...imageProps
}: ImageWithLoadingProps) {
  const [internalIsLoading, setInternalIsLoading] = useState(true);
  const [showSpinner, setShowSpinner] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  // Use external loading state if provided, otherwise use internal state
  const isLoading =
    externalIsLoading !== undefined ? externalIsLoading : internalIsLoading;

  const handleLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    setInternalIsLoading(false);
    if (onLoad) {
      onLoad(e);
    }
  };

  // Delay spinner appearance to avoid flash for cached images
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (isLoading) {
      // Small delay to prevent spinner blip for cached/fast-loading images
      timer = setTimeout(() => setShowSpinner(true), 150);
    } else {
      setShowSpinner(false);
    }
    return () => clearTimeout(timer);
  }, [isLoading]);

  // Check if image is already loaded (cached images) - only if not using external loading
  useEffect(() => {
    if (externalIsLoading === undefined) {
      const img = imgRef.current;
      if (img?.complete && img.naturalHeight !== 0) {
        setInternalIsLoading(false);
      }
    }
  }, [externalIsLoading]);

  return (
    <div
      className={`relative inline-block overflow-hidden ${containerClassName || ""}`}
    >
      <Image
        {...imageProps}
        ref={imgRef}
        className={`block object-cover ${className || ""}`}
        onLoad={handleLoad}
      />
      <div
        className={`absolute inset-0 z-10 flex items-center justify-center bg-black/50 transition-[opacity,visibility] duration-300 ease-out ${
          !showSpinner
            ? "pointer-events-none invisible opacity-0"
            : "visible opacity-100"
        }`}
      >
        <i
          className="pi pi-spin pi-spinner text-[var(--color-primary-a0)]"
          style={{ fontSize: "2rem" }}
          aria-hidden="true"
        />
      </div>
    </div>
  );
}
