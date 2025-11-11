"use client";

import type { ReactNode } from "react";
import { HeaderActionBar } from "./HeaderActionBar";

export interface PageHeaderProps {
  /**
   * Title to display on the left side of the header.
   */
  title: ReactNode;
  /**
   * Optional additional content to display between title and action bar.
   */
  children?: ReactNode;
}

/**
 * Reusable page header component.
 *
 * Displays a title on the left and the header action bar on the right.
 * Follows DRY by providing consistent header layout across pages.
 * Follows SRP by only handling header layout.
 *
 * Parameters
 * ----------
 * props : PageHeaderProps
 *     Component props including title and optional children.
 *
 * Examples
 * --------
 * ```tsx
 * <PageHeader title="My Library">
 *   <AddBooksButton />
 * </PageHeader>
 * ```
 */
export function PageHeader({ title, children }: PageHeaderProps) {
  return (
    <header className="flex items-center justify-between px-8 pt-6 pb-4">
      <h1 className="m-0 font-semibold text-[32px] text-[var(--color-text-a0)] leading-[1.2]">
        {title}
      </h1>
      <div className="flex shrink-0 items-center gap-3">
        {children}
        <HeaderActionBar />
      </div>
    </header>
  );
}
