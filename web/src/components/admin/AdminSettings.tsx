"use client";

import { useState } from "react";
import styles from "./AdminSettings.module.scss";
import { ConfigurationTab } from "./tabs/ConfigurationTab";
import { SystemTab } from "./tabs/SystemTab";
import { UsersTab } from "./tabs/UsersTab";

type TabId = "users" | "configuration" | "system";

export function AdminSettings() {
  const [activeTab, setActiveTab] = useState<TabId>("users");

  const tabs: { id: TabId; label: string }[] = [
    { id: "users", label: "Users" },
    { id: "configuration", label: "Configuration" },
    { id: "system", label: "System" },
  ];

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Admin Settings</h1>

      <div className={styles.tabsContainer}>
        <div className={styles.tabs}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`${styles.tab} ${
                activeTab === tab.id ? styles.active : ""
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className={styles.tabContent}>
          {activeTab === "users" && <UsersTab />}
          {activeTab === "configuration" && <ConfigurationTab />}
          {activeTab === "system" && <SystemTab />}
        </div>
      </div>
    </div>
  );
}
