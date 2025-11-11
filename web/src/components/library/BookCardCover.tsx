"use client";

import { ImageWithLoading } from "@/components/common/ImageWithLoading";

export interface BookCardCoverProps {
  /** Book title for alt text. */
  title: string;
  /** Thumbnail URL. */
  thumbnailUrl?: string | null;
}

/**
 * Book card cover image component.
 *
 * Displays book cover thumbnail or placeholder.
 * Follows SRP by focusing solely on cover display.
 */
export function BookCardCover({ title, thumbnailUrl }: BookCardCoverProps) {
  return (
    <div className="relative aspect-[2/3] w-full overflow-hidden">
      {thumbnailUrl ? (
        <ImageWithLoading
          src={thumbnailUrl}
          alt={`Cover for ${title}`}
          width={200}
          height={300}
          className="h-full w-full object-cover"
          containerClassName="w-full h-full"
          unoptimized
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-surface-a20 to-surface-a10">
          <span className="text-sm text-text-a40 uppercase tracking-[0.5px]">
            No Cover
          </span>
        </div>
      )}
    </div>
  );
}
