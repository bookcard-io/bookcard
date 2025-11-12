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

import { LibraryManagement } from "../library/LibraryManagement";
import styles from "./ConfigurationTab.module.scss";

export function ConfigurationTab() {
  return (
    <div className={styles.container}>
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Library Management</h2>
        <p className={styles.helpText}>
          Manage multiple Calibre libraries. Only one library can be active at a
          time. The active library is used for all book operations.
        </p>
        <LibraryManagement />
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Email Server Settings</h2>
        <p className={styles.placeholder}>
          Email server configuration will be implemented here.
        </p>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Basic Configuration</h2>
        <p className={styles.placeholder}>
          Basic system configuration will be implemented here.
        </p>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>UI Configuration</h2>
        <p className={styles.placeholder}>
          UI settings and preferences will be implemented here.
        </p>
      </div>
    </div>
  );
}
