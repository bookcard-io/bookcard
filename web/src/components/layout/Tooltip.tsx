// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

"use client";

import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/libs/utils";

export interface TooltipProps {
  /**
   * The content to display in the tooltip.
   */
  text: string | ReactNode;
  /**
   * The element that triggers the tooltip.
   */
  children: ReactNode;
  /**
   * Additional CSS classes to apply to the tooltip content.
   */
  className?: string;
}

/**
 * Tooltip component styled like Plex.
 *
 * Displays a dark tooltip with white text and an upward-pointing arrow.
 * Follows SRP by only handling tooltip rendering.
 *
 * Parameters
 * ----------
 * props : TooltipProps
 *     Component props including text and children.
 *
 * Examples
 * --------
 * ```tsx
 * <Tooltip text="View profile">
 *   <button>Profile</button>
 * </Tooltip>
 * ```
 */
export function Tooltip({ text, children, className }: TooltipProps) {
  const triggerRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });

  useEffect(() => {
    if (!isHovered || !triggerRef.current || !className) {
      return;
    }

    const updatePosition = () => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect();
        setPosition({
          top: rect.bottom + window.scrollY + 8,
          left: rect.left + window.scrollX + rect.width / 2,
        });
      }
    };

    updatePosition();

    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("resize", updatePosition);

    return () => {
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("resize", updatePosition);
    };
  }, [isHovered, className]);

  const usePortal = Boolean(className);

  const tooltipContent = (
    <div
      className={cn(
        "pointer-events-none invisible z-50 rounded-md bg-[var(--color-surface-a10)] px-3 py-1.5 text-[var(--color-text-a0)] text-sm opacity-0 shadow-lg transition-opacity duration-200",
        usePortal
          ? "-translate-x-1/2 fixed"
          : "-translate-x-1/2 absolute top-full left-1/2 mt-2",
        isHovered && "visible opacity-100",
        className?.includes("max-w") ? "" : "whitespace-nowrap",
        className,
      )}
      style={
        usePortal
          ? {
              top: `${position.top}px`,
              left: `${position.left}px`,
            }
          : undefined
      }
    >
      {text}
      {/* Arrow pointing down */}
      <div className="-translate-x-1/2 absolute bottom-full left-1/2 border-4 border-transparent border-b-[var(--color-surface-a10)]" />
    </div>
  );

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: tooltip wrapper pattern */
    <div
      ref={triggerRef}
      className="group relative inline-block"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {children}
      {usePortal
        ? isHovered && createPortal(tooltipContent, document.body)
        : tooltipContent}
    </div>
  );
}
