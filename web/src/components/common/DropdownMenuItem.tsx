"use client";

import { type ReactNode, useCallback } from "react";
import { cn } from "@/libs/utils";

export interface DropdownMenuItemProps {
  /** Optional icon element to display (string for PrimeIcons or ReactNode for custom icons). */
  icon?: ReactNode;
  /** Text label for the menu item. */
  label: string;
  /** Optional callback when item is clicked. */
  onClick?: () => void;
  /** Optional right-side content (e.g., chevron). */
  rightContent?: ReactNode;
  /** Whether this item should justify content between. */
  justifyBetween?: boolean;
}

/**
 * Dropdown menu item component.
 *
 * Displays a menu item with icon and text.
 * Follows DRY by centralizing menu item structure and styling.
 * Follows SRP by handling only menu item rendering.
 *
 * Parameters
 * ----------
 * props : DropdownMenuItemProps
 *     Component props including icon, label, and click handler.
 */
export function DropdownMenuItem({
  icon,
  label,
  onClick,
  rightContent,
  justifyBetween = false,
}: DropdownMenuItemProps) {
  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (onClick) {
        onClick();
      }
    },
    [onClick],
  );

  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-center gap-3 px-4 py-2.5 text-left",
        "text-sm text-text-a0",
        "hover:bg-surface-tonal-a20",
        "transition-colors duration-150",
        "focus:bg-surface-tonal-a20 focus:outline-none",
        justifyBetween && "justify-between",
      )}
      onClick={handleClick}
      role="menuitem"
    >
      <div className="flex items-center gap-3">
        {icon &&
          (typeof icon === "string" ? (
            <i
              className={cn(icon, "flex-shrink-0 text-base")}
              aria-hidden="true"
            />
          ) : (
            <div className="flex-shrink-0">{icon}</div>
          ))}
        <span>{label}</span>
      </div>
      {rightContent && <div className="flex-shrink-0">{rightContent}</div>}
    </button>
  );
}
