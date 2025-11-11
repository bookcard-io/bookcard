"use client";

import { HeaderActionButton } from "./HeaderActionButton";

/**
 * Admin button component for the header action bar.
 *
 * Displays admin settings button.
 * Follows SRP by only handling admin-specific rendering logic.
 * Follows DRY by using HeaderActionButton for common structure.
 */
export function AdminButton() {
  return (
    <HeaderActionButton
      href="/admin"
      tooltipText="Admin settings"
      ariaLabel="Go to admin settings"
    >
      <i className="pi pi-cog text-text-a30 text-xl" aria-hidden="true" />
    </HeaderActionButton>
  );
}
