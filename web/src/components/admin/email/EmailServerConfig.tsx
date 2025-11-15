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

import { Button } from "@/components/forms/Button";
import { useEmailServerConfig } from "@/hooks/useEmailServerConfig";
import { EmailServerStatusPill } from "./EmailServerStatusPill";
import { GmailFields } from "./GmailFields";
import { SmtpFields } from "./SmtpFields";

/**
 * Email server configuration component.
 *
 * Manages email server settings for sending e-books to devices.
 * Supports both SMTP and Gmail server types with conditional field visibility.
 *
 * Follows SOLID principles:
 * - SRP: Delegates business logic to useEmailServerConfig hook, API calls to service,
 *   and field rendering to sub-components
 * - IOC: Uses dependency injection via hook callbacks and component props
 * - SOC: Separates concerns into service layer, hook layer, and UI layer
 * - DRY: Reuses form components and centralizes state management
 *
 * Features:
 * - 3-column responsive grid layout
 * - Server type selection (SMTP/Gmail)
 * - Conditional field visibility based on server type
 * - Form validation and error handling
 * - Submit and cancel functionality
 */
export function EmailServerConfig() {
  const {
    config,
    formData,
    isLoading,
    isSaving,
    error,
    hasChanges,
    handleFieldChange,
    handleServerTypeChange,
    handleSubmit,
    handleCancel,
  } = useEmailServerConfig();

  if (isLoading) {
    return (
      <div className="py-6 text-center text-sm text-text-a30">
        Loading email server configuration...
      </div>
    );
  }

  const isSmtp = formData.server_type === "smtp";
  const isGmail = formData.server_type === "gmail";

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div className="rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm">
          {error}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void handleSubmit();
        }}
        className="flex flex-col gap-6"
      >
        {/* 3-Column Grid Layout */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {/* First Row: Server Type and Enabled (2 columns, 50% each) */}
          <div className="col-span-1 grid grid-cols-1 gap-6 md:col-span-3 md:grid-cols-2">
            {/* Server Type */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="server_type"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Server Type
              </label>
              <select
                id="server_type"
                value={formData.server_type || "smtp"}
                onChange={(e) =>
                  handleServerTypeChange(e.target.value as "smtp" | "gmail")
                }
                className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
              >
                <option value="smtp">SMTP</option>
                <option value="gmail">Gmail</option>
              </select>
            </div>

            {/* Enabled Toggle */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="enabled"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Enabled
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={formData.enabled ?? true}
                  onChange={(e) =>
                    handleFieldChange("enabled", e.target.checked)
                  }
                  className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 focus:ring-2 focus:ring-primary-a0"
                />
                <span className="text-sm text-text-a30">
                  Enable email server functionality
                </span>
              </div>
            </div>
          </div>

          {/* SMTP Fields - Only show when SMTP is selected */}
          {isSmtp && (
            <SmtpFields formData={formData} onFieldChange={handleFieldChange} />
          )}

          {/* Gmail Fields - Only show when Gmail is selected */}
          {isGmail && (
            <GmailFields
              formData={formData}
              onFieldChange={handleFieldChange}
            />
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between gap-3 border-surface-a20 border-t pt-4">
          <EmailServerStatusPill config={config} />
          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={handleCancel}
              disabled={!hasChanges || isSaving}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={isSaving}
              disabled={!hasChanges || isSaving}
            >
              Save Configuration
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
