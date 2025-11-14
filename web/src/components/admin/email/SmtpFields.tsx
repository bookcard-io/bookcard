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

import { NumberInput } from "@/components/forms/NumberInput";
import { TextInput } from "@/components/forms/TextInput";
import type { EmailServerConfigFormData } from "@/hooks/useEmailServerConfig";

export interface SmtpFieldsProps {
  /** Form data. */
  formData: EmailServerConfigFormData;
  /** Handler for field changes. */
  onFieldChange: <K extends keyof EmailServerConfigFormData>(
    field: K,
    value: EmailServerConfigFormData[K],
  ) => void;
}

/**
 * SMTP-specific form fields component.
 *
 * Renders all SMTP-related configuration fields.
 * Follows SRP by handling only SMTP field rendering.
 * Follows SOC by separating SMTP concerns from Gmail concerns.
 *
 * Parameters
 * ----------
 * props : SmtpFieldsProps
 *     Component props including form data and change handler.
 */
export function SmtpFields({ formData, onFieldChange }: SmtpFieldsProps) {
  return (
    <>
      {/* Second Row: SMTP Host, SMTP Port, Max Email Size (3 columns, 1/3 each) */}
      <TextInput
        id="smtp_host"
        label="SMTP Host"
        value={formData.smtp_host || ""}
        onChange={(e) => onFieldChange("smtp_host", e.target.value || null)}
        placeholder="smtp.example.com"
      />

      <NumberInput
        id="smtp_port"
        label="SMTP Port"
        value={formData.smtp_port ?? 587}
        onChange={(e) =>
          onFieldChange("smtp_port", parseInt(e.target.value, 10) || null)
        }
        min={1}
        max={65535}
        step={1}
      />

      <NumberInput
        id="max_email_size_mb"
        label="Max Email Size (MB)"
        value={formData.max_email_size_mb ?? 25}
        onChange={(e) =>
          onFieldChange("max_email_size_mb", parseInt(e.target.value, 10) || 25)
        }
        min={1}
        max={100}
        step={1}
      />

      {/* Third Row: SMTP Username and Password (2 columns, evenly spaced) */}
      <div className="col-span-1 grid grid-cols-1 gap-6 md:col-span-3 md:grid-cols-2">
        <TextInput
          id="smtp_username"
          label="SMTP Username"
          value={formData.smtp_username || ""}
          onChange={(e) =>
            onFieldChange("smtp_username", e.target.value || null)
          }
          placeholder="user@example.com"
        />

        <TextInput
          id="smtp_password"
          label="SMTP Password"
          type="password"
          value={formData.smtp_password || ""}
          onChange={(e) =>
            onFieldChange("smtp_password", e.target.value || undefined)
          }
          placeholder="Leave blank to keep current password"
        />
      </div>

      {/* Fourth Row: Encryption and From Email (2 columns) */}
      <div className="col-span-1 grid grid-cols-1 gap-6 md:col-span-3 md:grid-cols-2">
        {/* Encryption - Radio buttons */}
        <div className="flex flex-col gap-2">
          <div className="font-medium text-sm text-text-a10 leading-normal">
            Encryption
          </div>
          <div className="flex gap-4">
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                name="smtp_encryption"
                value="tls"
                checked={
                  (formData.smtp_use_tls ?? true) &&
                  !(formData.smtp_use_ssl ?? false)
                }
                onChange={() => {
                  onFieldChange("smtp_use_tls", true);
                  onFieldChange("smtp_use_ssl", false);
                }}
                className="h-4 w-4 cursor-pointer text-primary-a0 focus:ring-2 focus:ring-primary-a0"
              />
              <span className="text-sm text-text-a0">TLS</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                name="smtp_encryption"
                value="ssl"
                checked={
                  (formData.smtp_use_ssl ?? false) &&
                  !(formData.smtp_use_tls ?? true)
                }
                onChange={() => {
                  onFieldChange("smtp_use_ssl", true);
                  onFieldChange("smtp_use_tls", false);
                }}
                className="h-4 w-4 cursor-pointer text-primary-a0 focus:ring-2 focus:ring-primary-a0"
              />
              <span className="text-sm text-text-a0">SSL</span>
            </label>
          </div>
        </div>

        <TextInput
          id="smtp_from_email"
          label="From Email"
          value={formData.smtp_from_email || ""}
          onChange={(e) =>
            onFieldChange("smtp_from_email", e.target.value || null)
          }
          placeholder="automailer <sender@example.com>"
        />
      </div>
    </>
  );
}
