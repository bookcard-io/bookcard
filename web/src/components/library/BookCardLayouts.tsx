import type { ReactNode } from "react";
import { cn } from "@/libs/utils";

export interface BookCardLayoutProps {
  cover: ReactNode;
  metadata: ReactNode;
  actions: ReactNode;
  className?: string;
  onClick?: () => void;
  onKeyDown?: (e: React.KeyboardEvent) => void;
  ariaLabel?: string;
  selected?: boolean;
}

export const BookCardDefaultLayout: React.FC<BookCardLayoutProps> = ({
  cover,
  metadata,
  actions,
  className,
  onClick,
  onKeyDown,
  ariaLabel,
  selected,
}) => (
  /* biome-ignore lint/a11y/useSemanticElements: Cannot use <button> here because BookCardReadingCorner contains a button, and nested buttons are invalid HTML. */
  <div
    role="button"
    tabIndex={0}
    className={cn(
      "group h-full cursor-pointer overflow-hidden rounded",
      "w-full border-2 border-transparent bg-gradient-to-b from-surface-a0 to-surface-a10 p-0 text-left",
      "transition-[transform,box-shadow,border-color] duration-200 ease-out",
      "hover:-translate-y-0.5 hover:shadow-card-hover",
      "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
      "focus:not-focus-visible:outline-none focus:outline-none",
      selected && "border-primary-a0 shadow-primary-glow outline-none",
      // Mobile: grid layout
      "grid grid-cols-[75px_1fr] grid-rows-[1fr_auto] gap-0",
      // Desktop: vertical flex layout
      "md:flex md:flex-col",
      className,
    )}
    onClick={onClick}
    onKeyDown={onKeyDown}
    aria-label={ariaLabel}
    data-book-card
  >
    {/* Cover area: Mobile col 1 row 1-2, Desktop full width */}
    <div className="relative col-start-1 row-span-2 row-start-1 md:col-span-1 md:row-span-1">
      {cover}
    </div>

    {/* Metadata area: Mobile col 2 row 1, Desktop full width */}
    <div className="col-start-2 row-start-1 h-full md:col-span-1 md:h-auto">
      {metadata}
    </div>

    {/* Mobile actions: Mobile col 2 row 2, Desktop hidden */}
    <div className="col-start-2 row-start-2 flex items-center justify-end gap-2 p-2 md:hidden">
      {actions}
    </div>
  </div>
);

export const BookCardCompactLayout: React.FC<BookCardLayoutProps> = ({
  cover,
  metadata,
  actions,
  className,
  onClick,
  onKeyDown,
  ariaLabel,
  selected,
}) => (
  /* biome-ignore lint/a11y/useSemanticElements: Cannot use <button> here because BookCardReadingCorner contains a button, and nested buttons are invalid HTML. */
  <div
    role="button"
    tabIndex={0}
    className={cn(
      "group h-full cursor-pointer overflow-hidden rounded",
      "w-full border-2 border-transparent bg-gradient-to-b from-surface-a0 to-surface-a10 p-0 text-left",
      "transition-[transform,box-shadow,border-color] duration-200 ease-out",
      "hover:-translate-y-0.5 hover:shadow-card-hover",
      "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
      "focus:not-focus-visible:outline-none focus:outline-none",
      selected && "border-primary-a0 shadow-primary-glow outline-none",
      // Always grid layout
      "grid grid-cols-[75px_1fr] grid-rows-[1fr_auto] gap-0",
      className,
    )}
    onClick={onClick}
    onKeyDown={onKeyDown}
    aria-label={ariaLabel}
    data-book-card
  >
    <div className="relative col-start-1 row-span-2 row-start-1">{cover}</div>
    <div className="col-start-2 row-start-1 h-full">{metadata}</div>
    <div className="col-start-2 row-start-2 flex items-center justify-end gap-2 p-2">
      {actions}
    </div>
  </div>
);
