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

import { StatusPill } from "@/components/common/StatusPill";
import type { EmailServerConfigData } from "@/services/emailServerConfigService";

export interface EmailServerStatusPillProps {
  /** Current saved configuration. */
  config: EmailServerConfigData | null;
}

/**
 * Status pill component for email server configuration.
 *
 * Displays an "Active" pill when a server configuration exists and is enabled.
 * Follows SRP by handling only email server-specific status logic.
 * Uses the generic StatusPill component for rendering.
 *
 * Parameters
 * ----------
 * props : EmailServerStatusPillProps
 *     Component props including configuration.
 */
export function EmailServerStatusPill({ config }: EmailServerStatusPillProps) {
  if (!config || !(config.enabled ?? false)) {
    return <div />;
  }

  return <StatusPill label="Active" icon="pi pi-check" variant="success" />;
}
