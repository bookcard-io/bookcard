"use client";

import Image, { type ImageProps } from "next/image";
import { useEffect, useRef, useState } from "react";
import styles from "./ImageWithLoading.module.scss";

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
    <div className={`${styles.container} ${containerClassName || ""}`}>
      <Image
        {...imageProps}
        ref={imgRef}
        className={`${styles.image} ${className || ""}`}
        onLoad={handleLoad}
      />
      <div
        className={`${styles.curtain} ${!isLoading ? styles.curtainHidden : ""}`}
      >
        <i
          className="pi pi-spin pi-spinner"
          style={{ fontSize: "2rem" }}
          aria-hidden="true"
        />
      </div>
    </div>
  );
}
