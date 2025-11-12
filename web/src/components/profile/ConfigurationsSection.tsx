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
import { SettingsProvider, useSettings } from "@/contexts/SettingsContext";
import { useTabScroll } from "@/hooks/useTabScroll";
import { cn } from "@/libs/utils";
import { BlurAfterClickProvider } from "./BlurAfterClickContext";
import { AutoDismissBookEditModalConfiguration } from "./config/AutoDismissBookEditModalConfiguration";
import { AutoOpenBookDetailsConfiguration } from "./config/AutoOpenBookDetailsConfiguration";
import { DefaultPageSizeConfiguration } from "./config/DefaultPageSizeConfiguration";
import { DefaultSortFieldConfiguration } from "./config/DefaultSortFieldConfiguration";
import { DefaultSortOrderConfiguration } from "./config/DefaultSortOrderConfiguration";
import { DefaultViewModeConfiguration } from "./config/DefaultViewModeConfiguration";
import { DeleteSettingsGroup } from "./config/DeleteSettingsGroup";
import { DisplayModeConfiguration } from "./config/DisplayModeConfiguration";
import { EnabledMetadataProvidersConfiguration } from "./config/EnabledMetadataProvidersConfiguration";
import { LanguagesConfiguration } from "./config/LanguagesConfiguration";
import { MetadataProvidersConfiguration } from "./config/MetadataProvidersConfiguration";
import { ReplaceCoverOnMetadataSelectionConfiguration } from "./config/ReplaceCoverOnMetadataSelectionConfiguration";
import {
  CONFIGURATION_TABS,
  DEFAULT_TAB_ID,
  type TabId,
} from "./configurationsSectionConstants";

/**
 * Tab content container component.
 *
 * Renders tab content with proper data attribute for scroll detection.
 * Follows SRP by handling only content rendering.
 *
 * Parameters
 * ----------
 * children : ReactNode[]
 *     Array of React components to render as tab content.
 */
function TabContent({ children }: { children: React.ReactNode[] }) {
  return (
    <div data-tab-content="true" className="flex flex-col gap-6">
      {children}
    </div>
  );
}

/**
 * Configurations section content component.
 *
 * Rendered inside SettingsProvider to access settings context.
 * Follows SRP by handling only UI rendering and tab state management.
 * Follows IOC by using configurable scroll hook.
 * Follows SOC by delegating scroll behavior to useTabScroll hook.
 */
function ConfigurationsSectionContent() {
  const [activeTab, setActiveTab] = useState<TabId>(DEFAULT_TAB_ID);
  const { isSaving } = useSettings();
  const { headerRef, contentRef, scrollToBottom } = useTabScroll();

  /**
   * Handles tab click event.
   *
   * Updates active tab state and triggers scroll to bottom-most setting.
   *
   * Parameters
   * ----------
   * tabId : TabId
   *     ID of the tab to activate.
   */
  const handleTabClick = (tabId: TabId) => {
    setActiveTab(tabId);
    scrollToBottom();
  };

  /**
   * Gets the content components for the active tab.
   *
   * Follows SRP by handling only content mapping logic.
   * Follows DRY by centralizing content component definitions.
   *
   * Returns
   * -------
   * React.ReactNode[]
   *     Array of React components to render in the active tab.
   */
  const getActiveTabContent = (): React.ReactNode[] => {
    switch (activeTab) {
      case "display":
        return [
          <DisplayModeConfiguration key="display-mode" />,
          <DefaultViewModeConfiguration key="view-mode" />,
          <DefaultPageSizeConfiguration key="page-size" />,
          <LanguagesConfiguration key="languages" />,
        ];
      case "sorting":
        return [
          <DefaultSortFieldConfiguration key="sort-field" />,
          <DefaultSortOrderConfiguration key="sort-order" />,
        ];
      case "content":
        return [
          <EnabledMetadataProvidersConfiguration key="enabled-metadata-providers" />,
          <MetadataProvidersConfiguration key="metadata-providers" />,
          <ReplaceCoverOnMetadataSelectionConfiguration key="replace-cover-on-metadata-select" />,
          <AutoDismissBookEditModalConfiguration key="auto-dismiss-modal" />,
        ];
      case "navigation":
        return [<AutoOpenBookDetailsConfiguration key="auto-open" />];
      case "deletion":
        return [<DeleteSettingsGroup key="delete-settings" />];
      default:
        return [];
    }
  };

  const activeTabContent = getActiveTabContent();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-2">
        <h2 ref={headerRef} className="m-0 font-semibold text-text-a0 text-xl">
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
            {CONFIGURATION_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={cn(
                  "-mb-px relative cursor-pointer border-0 border-transparent border-b-2 bg-transparent px-6 py-3 font-medium text-sm text-text-a30 transition-[color,border-color] duration-200",
                  "hover:text-text-a10",
                  activeTab === tab.id &&
                    "border-b-[var(--color-primary-a0)] text-text-a0",
                )}
                onClick={() => handleTabClick(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div ref={contentRef} className="px-0 py-3.5">
            <TabContent>{activeTabContent}</TabContent>
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
