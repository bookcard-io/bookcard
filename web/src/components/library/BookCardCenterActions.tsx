"use client";

import { FaBookReader } from "react-icons/fa";
import { ImSpinner8 } from "react-icons/im";
import { MdInfoOutline } from "react-icons/md";
import { cn } from "@/libs/utils";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface BookCardCenterActionsProps {
  onReadClick?: () => void;
  onInfoClick?: () => void;
  isReading?: boolean;
}

export function BookCardCenterActions({
  onReadClick,
  onInfoClick,
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
      {onInfoClick && (
        /* biome-ignore lint/a11y/useSemanticElements: Cannot use button tag because it would result in nested buttons (BookCard is a button) */
        <div
          role="button"
          tabIndex={0}
          onClick={(e) => handleOverlayButtonClick(e, onInfoClick)}
          onKeyDown={createEnterSpaceHandler(onInfoClick)}
          className="transform cursor-pointer transition-transform hover:scale-110 focus:outline-none"
          aria-label="View Info"
        >
          <MdInfoOutline className="text-5xl drop-shadow-lg" />
        </div>
      )}
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
            "transform transition-transform focus:outline-none",
            onReadClick
              ? "cursor-pointer hover:scale-110"
              : "scale-100 cursor-default",
          )}
          aria-label="Read Book"
        >
          {isReading ? (
            <ImSpinner8 className="animate-spin text-5xl text-white drop-shadow-lg" />
          ) : (
            <FaBookReader className="text-5xl drop-shadow-lg" />
          )}
        </div>
      )}
    </div>
  );
}
