"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { Tooltip } from "./Tooltip";

export interface HeaderActionButtonProps {
  /**
   * URL to navigate to when the button is clicked.
   */
  href: string;
  /**
   * Tooltip text to display on hover.
   */
  tooltipText: string;
  /**
   * Accessible label for the button.
   */
  ariaLabel: string;
  /**
   * Content to render inside the button.
   */
  children: ReactNode;
}

/**
 * Base component for header action bar buttons.
 *
 * Provides consistent styling and tooltip functionality for all action bar buttons.
 * Follows DRY by centralizing common button structure.
 * Follows SRP by only handling button structure and styling.
 *
 * Parameters
 * ----------
 * props : HeaderActionButtonProps
 *     Component props including href, tooltip, and children.
 */
export function HeaderActionButton({
  href,
  tooltipText,
  ariaLabel,
  children,
}: HeaderActionButtonProps) {
  return (
    <Tooltip text={tooltipText}>
      <Link
        href={href}
        className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-full border border-surface-a20 bg-surface-tonal-a10 transition-colors duration-200 hover:bg-surface-tonal-a20"
        aria-label={ariaLabel}
      >
        {children}
      </Link>
    </Tooltip>
  );
}
