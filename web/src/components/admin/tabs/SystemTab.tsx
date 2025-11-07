"use client";

import styles from "./SystemTab.module.scss";

export function SystemTab() {
  return (
    <div className={styles.container}>
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Scheduled Tasks</h2>
        <p className={styles.placeholder}>
          Scheduled task configuration will be implemented here.
        </p>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Administration</h2>
        <p className={styles.placeholder}>
          System administration actions will be implemented here.
        </p>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Version Information</h2>
        <p className={styles.placeholder}>
          Version and update information will be displayed here.
        </p>
      </div>
    </div>
  );
}
