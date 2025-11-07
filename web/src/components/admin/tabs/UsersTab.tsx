"use client";

import styles from "./UsersTab.module.scss";

export function UsersTab() {
  return (
    <div className={styles.container}>
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Users</h2>
        <p className={styles.placeholder}>
          User management interface will be implemented here.
        </p>
      </div>
    </div>
  );
}
