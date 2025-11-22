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

import type React from "react";
import type { AuthorUpdate, AuthorWithMetadata } from "@/types/author";
import { AdvancedTab } from "./AdvancedTab";
import { GeneralTab } from "./GeneralTab";
import { PhotoTab } from "./PhotoTab";
import { TagsTab } from "./TagsTab";

export type TabKey = "general" | "tags" | "photo" | "advanced";

export interface TabConfig {
  key: TabKey;
  label: string;
  render: (props: TabRenderProps) => React.ReactNode;
}

export interface TabRenderProps {
  author: AuthorWithMetadata;
  form: AuthorUpdate;
  onFieldChange: <K extends keyof AuthorUpdate>(
    field: K,
    value: AuthorUpdate[K],
  ) => void;
}

/**
 * Registry for tab configurations.
 *
 * Follows Open/Closed Principle - new tabs can be added without
 * modifying existing code. Follows IOC by accepting render functions.
 */
export class TabRegistry {
  private tabs: Map<TabKey, TabConfig> = new Map();

  /**
   * Register a tab configuration.
   *
   * Parameters
   * ----------
   * config : TabConfig
   *     The tab configuration to register.
   */
  register(config: TabConfig): void {
    this.tabs.set(config.key, config);
  }

  /**
   * Get a tab configuration by key.
   *
   * Parameters
   * ----------
   * key : TabKey
   *     The tab key.
   *
   * Returns
   * -------
   * TabConfig | undefined
   *     The tab configuration, or undefined if not found.
   */
  get(key: TabKey): TabConfig | undefined {
    return this.tabs.get(key);
  }

  /**
   * Get all registered tabs.
   *
   * Returns
   * -------
   * TabConfig[]
   *     Array of all registered tab configurations.
   */
  getAll(): TabConfig[] {
    return Array.from(this.tabs.values());
  }
}

/**
 * Create the default tab registry with built-in tabs.
 *
 * Follows IOC by returning a registry that can be extended.
 */
export function createDefaultTabRegistry(): TabRegistry {
  const registry = new TabRegistry();

  registry.register({
    key: "general",
    label: "General",
    render: ({ author, form, onFieldChange }) => (
      <GeneralTab author={author} form={form} onFieldChange={onFieldChange} />
    ),
  });

  registry.register({
    key: "tags",
    label: "Tags",
    render: ({ author, form, onFieldChange }) => (
      <TagsTab author={author} form={form} onFieldChange={onFieldChange} />
    ),
  });

  registry.register({
    key: "photo",
    label: "Photo",
    render: ({ author, form, onFieldChange }) => (
      <PhotoTab author={author} form={form} onFieldChange={onFieldChange} />
    ),
  });

  registry.register({
    key: "advanced",
    label: "Advanced",
    render: ({ author, form, onFieldChange }) => (
      <div className="flex h-full w-full flex-col">
        <AdvancedTab
          author={author}
          form={form}
          onFieldChange={onFieldChange}
        />
      </div>
    ),
  });

  return registry;
}
