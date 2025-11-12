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

import styles from "./UsersTable.module.scss";

export interface User {
  id: number;
  username: string;
  email: string;
  profile_picture: string | null;
  is_admin: boolean;
  default_ereader_email: string | null;
  roles: Array<{
    id: number;
    name: string;
    description: string | null;
  }>;
}

export interface UsersTableProps {
  users: User[];
  isLoading?: boolean;
}

export function UsersTable({ users, isLoading }: UsersTableProps) {
  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading users...</div>
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.empty}>No users found</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.table}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerCell}>Username</div>
          <div className={styles.headerCell}>Email</div>
          <div className={styles.headerCell}>Default Device</div>
          <div className={styles.headerCell}>Roles</div>
          <div className={styles.headerCell}>Admin</div>
        </div>

        {/* Rows */}
        <div className={styles.body}>
          {users.map((user) => (
            <div key={user.id} className={styles.row}>
              <div className={styles.cell}>{user.username}</div>
              <div className={styles.cell}>{user.email}</div>
              <div className={styles.cell}>
                {user.default_ereader_email || (
                  <span className={styles.emptyValue}>—</span>
                )}
              </div>
              <div className={styles.cell}>
                {user.roles.length > 0 ? (
                  <div className={styles.roles}>
                    {user.roles.map((role) => (
                      <span key={role.id} className={styles.roleTag}>
                        {role.name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className={styles.emptyValue}>—</span>
                )}
              </div>
              <div className={styles.cell}>
                {user.is_admin ? (
                  <span className={styles.adminBadge}>Admin</span>
                ) : (
                  <span className={styles.emptyValue}>—</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
