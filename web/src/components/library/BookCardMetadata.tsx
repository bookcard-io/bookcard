"use client";

export interface BookCardMetadataProps {
  /** Book title. */
  title: string;
  /** Book authors. */
  authors: string[];
}

/**
 * Book card metadata component (title and authors).
 *
 * Displays book title and author information.
 * Follows SRP by focusing solely on metadata display.
 */
export function BookCardMetadata({ title, authors }: BookCardMetadataProps) {
  const authorsText =
    authors.length > 0 ? authors.join(", ") : "Unknown Author";

  return (
    <div className="flex min-h-16 flex-col gap-1 bg-surface-a10 p-[0.75rem]">
      <h3
        className="m-0 line-clamp-2 font-[500] text-[0.875rem] text-text-a0 leading-[1.3]"
        title={title}
      >
        {title}
      </h3>
      <p
        className="m-0 line-clamp-1 text-text-a20 text-xs leading-[1.3]"
        title={authorsText}
      >
        {authorsText}
      </p>
    </div>
  );
}
