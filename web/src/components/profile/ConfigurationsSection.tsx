"use client";

import { useState } from "react";
import { SettingsProvider, useSettings } from "@/contexts/SettingsContext";
import { cn } from "@/libs/utils";
import { BlurAfterClickProvider } from "./BlurAfterClickContext";
import { AutoOpenBookDetailsConfiguration } from "./config/AutoOpenBookDetailsConfiguration";
import { DefaultDeleteFilesFromDriveConfiguration } from "./config/DefaultDeleteFilesFromDriveConfiguration";
import { DefaultPageSizeConfiguration } from "./config/DefaultPageSizeConfiguration";
import { DefaultSortFieldConfiguration } from "./config/DefaultSortFieldConfiguration";
import { DefaultSortOrderConfiguration } from "./config/DefaultSortOrderConfiguration";
import { DefaultViewModeConfiguration } from "./config/DefaultViewModeConfiguration";
import { DeleteWarningConfiguration } from "./config/DeleteWarningConfiguration";
import { DisplayModeConfiguration } from "./config/DisplayModeConfiguration";
import { LanguagesConfiguration } from "./config/LanguagesConfiguration";
import { MetadataProvidersConfiguration } from "./config/MetadataProvidersConfiguration";

type TabId = "display" | "sorting" | "navigation" | "deletion" | "content";

/**
 * Configurations section content component.
 *
 * Rendered inside SettingsProvider to access settings context.
 * Follows SRP by handling only UI rendering.
 */
function ConfigurationsSectionContent() {
  const [activeTab, setActiveTab] = useState<TabId>("display");
  const { isSaving } = useSettings();

  const tabs: { id: TabId; label: string }[] = [
    { id: "display", label: "Display & Layout" },
    { id: "sorting", label: "Sorting & Organization" },
    { id: "content", label: "Content & Metadata" },
    { id: "navigation", label: "Navigation & Interaction" },
    { id: "deletion", label: "Deletion Preferences" },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-2">
        <h2 className="m-0 font-semibold text-text-a0 text-xl">
          Configurations
        </h2>
        {isSaving && (
          <div className="flex items-center gap-2 text-sm text-text-a30">
            <i className="pi pi-spin pi-spinner" aria-hidden="true" />
            <span>Saving...</span>
          </div>
        )}
      </div>

      <BlurAfterClickProvider>
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
            {activeTab === "display" && (
              <div className="flex flex-col gap-6">
                <DisplayModeConfiguration />
                <DefaultViewModeConfiguration />
                <DefaultPageSizeConfiguration />
                <LanguagesConfiguration />
              </div>
            )}

            {activeTab === "sorting" && (
              <div className="flex flex-col gap-6">
                <DefaultSortFieldConfiguration />
                <DefaultSortOrderConfiguration />
              </div>
            )}

            {activeTab === "content" && (
              <div className="flex flex-col gap-6">
                <MetadataProvidersConfiguration />
              </div>
            )}

            {activeTab === "navigation" && (
              <div className="flex flex-col gap-6">
                <AutoOpenBookDetailsConfiguration />
              </div>
            )}

            {activeTab === "deletion" && (
              <div className="flex flex-col gap-6">
                <DeleteWarningConfiguration />
                <DefaultDeleteFilesFromDriveConfiguration />
              </div>
            )}
          </div>
        </div>
      </BlurAfterClickProvider>
    </div>
  );
}

/**
 * Configurations section for user preferences.
 *
 * Orchestrates display of all configuration options in tabs with logical groupings.
 * Wraps content in SettingsProvider to manage settings state and persistence.
 * Follows SRP by delegating to specialized configuration components.
 * Follows SOC by separating each configuration concern.
 * Follows IOC by accepting configurable debounce delay.
 *
 * Parameters
 * ----------
 * debounceMs : number
 *     Debounce delay in milliseconds for settings updates (default: 500).
 */
export function ConfigurationsSection({
  debounceMs = 300,
}: {
  debounceMs?: number;
}) {
  return (
    <SettingsProvider debounceMs={debounceMs}>
      <ConfigurationsSectionContent />
    </SettingsProvider>
  );
}
