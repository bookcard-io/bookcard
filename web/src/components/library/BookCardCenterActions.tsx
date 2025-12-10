"use client";

import { FaBookReader } from "react-icons/fa";
import { ImSpinner8 } from "react-icons/im";
import { cn } from "@/libs/utils";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface BookCardCenterActionsProps {
  onReadClick?: () => void;
  isReading?: boolean;
}

export function BookCardCenterActions({
  onReadClick,
  isReading,
}: BookCardCenterActionsProps) {
  const handleOverlayButtonClick = (
    e: React.MouseEvent,
    handler?: () => void,
  ) => {
    e.stopPropagation();
    handler?.();
  };

  return (
    <div className="flex flex-col items-center gap-4 text-white opacity-0 transition-opacity duration-200 group-hover:opacity-100">
      {(onReadClick || isReading) && (
        /* biome-ignore lint/a11y/useSemanticElements: Cannot use button tag because it would result in nested buttons (BookCard is a button) */
        <div
          role="button"
          tabIndex={onReadClick ? 0 : -1}
          onClick={(e) =>
            onReadClick && handleOverlayButtonClick(e, onReadClick)
          }
          onKeyDown={
            onReadClick ? createEnterSpaceHandler(onReadClick) : undefined
          }
          className={cn(
            "transform text-white transition-all focus:outline-none",
            onReadClick
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
