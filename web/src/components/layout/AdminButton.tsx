"use client";

import Link from "next/link";
import { cn } from "@/libs/utils";
import { Tooltip } from "./Tooltip";

/**
 * Admin button component for the header action bar.
 *
 * Displays admin settings button.
 * Follows SRP by only handling admin button rendering.
 */
export function AdminButton() {
  return (
    <Tooltip text="Admin settings">
      <Link
        href="/admin"
        className={cn(
          "flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-full border border-surface-a20 bg-surface-tonal-a10 transition-colors duration-200 hover:bg-surface-tonal-a20",
        )}
        aria-label="Go to admin settings"
      >
        <i className="pi pi-cog text-text-a30 text-xl" aria-hidden="true" />
      </Link>
    </Tooltip>
  );
}
