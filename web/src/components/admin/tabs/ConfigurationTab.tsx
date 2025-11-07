"use client";

import styles from "./ConfigurationTab.module.scss";

export function ConfigurationTab() {
  return (
    <div className={styles.container}>
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Email Server Settings</h2>
        <p className={styles.placeholder}>
          Email server configuration will be implemented here.
        </p>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Database Configuration</h2>
        <p className={styles.placeholder}>
          Calibre database configuration will be implemented here.
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
