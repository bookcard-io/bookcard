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

import { useState } from "react";
import { BlurAfterClickProvider } from "@/components/profile/BlurAfterClickContext";
import { cn } from "@/libs/utils";
import { ConfigurationTab } from "./tabs/ConfigurationTab";
import { PluginsTab } from "./tabs/PluginsTab";
import { ScheduledTasksTab } from "./tabs/ScheduledTasksTab";
import { SystemTab } from "./tabs/SystemTab";
import { UsersAndRolesTab } from "./tabs/UsersAndRolesTab";

type TabId =
  | "users"
  | "configuration"
  | "system"
  | "scheduled-tasks"
  | "plugins";

export function AdminSettings() {
  const [activeTab, setActiveTab] = useState<TabId>("users");

  const tabs: { id: TabId; label: string }[] = [
    { id: "users", label: "Users & Permissions" },
    { id: "configuration", label: "Configuration" },
    { id: "system", label: "System" },
    { id: "scheduled-tasks", label: "Scheduled Tasks" },
    { id: "plugins", label: "Plugins" },
  ];

  return (
    <div className="p-6 px-8">
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

        <BlurAfterClickProvider>
          <div className="px-0 py-3.5">
            {activeTab === "users" && <UsersAndRolesTab />}
            {activeTab === "configuration" && <ConfigurationTab />}
            {activeTab === "system" && <SystemTab />}
            {activeTab === "scheduled-tasks" && <ScheduledTasksTab />}
            {activeTab === "plugins" && <PluginsTab />}
          </div>
        </BlurAfterClickProvider>
      </div>
    </div>
  );
}
