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

import { EmailServerConfig } from "../email/EmailServerConfig";
import styles from "./SystemTab.module.scss";

/**
 * System tab component for admin panel.
 *
 * Displays email server configuration and system administration settings.
 * Follows SRP by orchestrating specialized components.
 * Follows SOC by separating concerns into focused components.
 */
export function SystemTab() {
  return (
    <div className={styles.container}>
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Email Server Settings</h2>
        <p className="mb-4 text-sm text-text-a30 leading-relaxed">
          Configure email server settings for sending e-books to devices.
          Supports both SMTP and Gmail server types.
        </p>
        <EmailServerConfig />
      </div>
    </div>
  );
}
