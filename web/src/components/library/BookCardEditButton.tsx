"use client";

import { cn } from "@/libs/utils";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface BookCardEditButtonProps {
  /** Book title for accessibility. */
  bookTitle: string;
  /** Handler for edit action. */
  onEdit: () => void;
}

/**
 * Edit button overlay for book card.
 *
 * Handles edit button interaction.
 * Follows SRP by focusing solely on edit button UI and behavior.
 * Uses IOC via callback prop.
 */
export function BookCardEditButton({
  bookTitle,
  onEdit,
}: BookCardEditButtonProps) {
  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    onEdit();
  };

  const handleKeyDown = createEnterSpaceHandler(() => {
    handleClick({} as React.MouseEvent<HTMLDivElement>);
  });

  return (
    /* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */
    <div
      className={cn(
        "edit-button pointer-events-auto flex cursor-default items-center justify-center",
        "text-text-a0 transition-[background-color,transform,opacity] duration-200 ease-in-out",
        "focus:shadow-focus-ring focus:outline-none",
        "absolute bottom-3 left-3 h-10 w-10 rounded-full",
        "border-none bg-white/20 backdrop-blur-sm",
        "hover:scale-110 hover:bg-white/30",
        "active:scale-95",
        "[&_i]:block [&_i]:text-lg",
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`Edit ${bookTitle}`}
      onKeyDown={handleKeyDown}
    >
      <i className="pi pi-pencil" aria-hidden="true" />
    </div>
  );
}
