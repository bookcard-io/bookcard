"use client";

import { useState } from "react";
import { cn } from "@/libs/utils";
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
    <div className="p-6 px-8">
      <h1 className="m-0 mb-8 font-semibold text-[32px] text-text-a0 leading-[1.2]">
        Admin Settings
      </h1>

      <div className="flex flex-col gap-6">
        <div className="flex gap-2 border-[var(--color-surface-a20)] border-b">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={cn(
                "-mb-px relative cursor-pointer border-0 border-transparent border-b-2 bg-transparent px-6 py-3 font-medium text-sm text-text-a30 transition-[color,border-color] duration-200",
                "hover:text-text-a10",
                activeTab === tab.id &&
                  "border-b-[var(--color-primary-a0)] text-text-a0",
              )}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="px-0 py-3.5">
          {activeTab === "users" && <UsersTab />}
          {activeTab === "configuration" && <ConfigurationTab />}
          {activeTab === "system" && <SystemTab />}
        </div>
      </div>
    </div>
  );
}
