"use client";

import { useEffect, useState } from "react";
import { type User, UsersTable } from "../UsersTable";
import styles from "./UsersTab.module.scss";

export function UsersTab() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setIsLoading(true);

        const response = await fetch("/api/admin/users?limit=100&offset=0", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        const data = await response.json();
        setUsers(data);
      } catch (_err) {
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, []);

  return (
    <div className={styles.container}>
      <h2 className={styles.sectionTitle}>Users</h2>
      <UsersTable users={users} isLoading={isLoading} />
    </div>
  );
}
