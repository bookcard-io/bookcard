"use client";

import { FaBookReader } from "react-icons/fa";
import { ImSpinner8 } from "react-icons/im";
import { useBookNavigation } from "@/hooks/useBookNavigation";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface BookCardCenterActionsProps {
  book: Book;
  onReadClick?: () => void;
  isReading?: boolean;
}

export function BookCardCenterActions({
  book,
  onReadClick: propOnReadClick,
  isReading: propIsReading,
}: BookCardCenterActionsProps) {
  const { isNavigating, navigateToReader, readableFormat } =
    useBookNavigation(book);

  // Use props if provided, otherwise use hook values
  const isReading = propIsReading ?? isNavigating;

  // If propOnReadClick is provided, use it.
  // Otherwise, use navigateToReader IF we have a readable format.
  // If no readable format, handleReadClick is undefined (button hidden).
  const handleReadClick =
    propOnReadClick ?? (readableFormat ? navigateToReader : undefined);

  const handleOverlayButtonClick = (
    e: React.MouseEvent,
    handler?: () => void,
  ) => {
    e.stopPropagation();
    handler?.();
  };

  const showButton = !!handleReadClick || isReading;

  return (
    <div className="flex flex-col items-center gap-4 text-white opacity-0 transition-opacity duration-200 group-hover:opacity-100">
      {showButton && (
        /* biome-ignore lint/a11y/useSemanticElements: Cannot use button tag because it would result in nested buttons (BookCard is a button) */
        <div
          role="button"
          tabIndex={handleReadClick ? 0 : -1}
          onClick={(e) =>
            handleReadClick && handleOverlayButtonClick(e, handleReadClick)
          }
          onKeyDown={
            handleReadClick
              ? createEnterSpaceHandler(handleReadClick)
              : undefined
          }
          className={cn(
            "transform text-white transition-all focus:outline-none",
            handleReadClick
              ? "cursor-pointer rounded-full border-2 border-white p-2 hover:border-transparent hover:bg-[var(--color-primary-a0)] hover:text-[var(--color-text-primary-a0)]"
              : "scale-100 cursor-default",
          )}
          aria-label="Read Book"
        >
          {isReading ? (
            <ImSpinner8 className="animate-spin text-4xl drop-shadow-lg transition-colors duration-200" />
          ) : (
            <FaBookReader className="text-4xl drop-shadow-lg transition-colors duration-200" />
          )}
        </div>
      )}
    </div>
  );
}
