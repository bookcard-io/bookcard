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

import { TextArea } from "@/components/forms/TextArea";
import type { EmailServerConfigFormData } from "@/hooks/useEmailServerConfig";

export interface GmailFieldsProps {
  /** Form data. */
  formData: EmailServerConfigFormData;
  /** Handler for field changes. */
  onFieldChange: <K extends keyof EmailServerConfigFormData>(
    field: K,
    value: EmailServerConfigFormData[K],
  ) => void;
}

/**
 * Gmail-specific form fields component.
 *
 * Renders Gmail OAuth token configuration field.
 * Follows SRP by handling only Gmail field rendering.
 * Follows SOC by separating Gmail concerns from SMTP concerns.
 *
 * Parameters
 * ----------
 * props : GmailFieldsProps
 *     Component props including form data and change handler.
 */
export function GmailFields({ formData, onFieldChange }: GmailFieldsProps) {
  return (
    <div className="col-span-1 md:col-span-3">
      <TextArea
        id="gmail_token"
        label="Gmail OAuth Token"
        value={
          formData.gmail_token
            ? JSON.stringify(formData.gmail_token, null, 2)
            : ""
        }
        onChange={(e) => {
          try {
            const value = e.target.value.trim();
            if (!value) {
              onFieldChange("gmail_token", null);
              return;
            }
            const parsed = JSON.parse(value);
            onFieldChange("gmail_token", parsed);
          } catch {
            // Invalid JSON, but allow typing
            // Will be validated on submit
          }
        }}
        placeholder='{"access_token": "...", "refresh_token": "..."}'
      />
    </div>
  );
}
