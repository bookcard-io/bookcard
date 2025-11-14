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

import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { SidebarNavItem } from "./SidebarNavItem";
import { SidebarSection } from "./SidebarSection";

export interface LibrarySectionProps {
  /** Whether the sidebar is collapsed. */
  isCollapsed: boolean;
  /** Whether the section is expanded. */
  isExpanded: boolean;
  /** Callback when section header is clicked. */
  onToggle: () => void;
  /** Callback when home is clicked. */
  onHomeClick: () => void;
}

/**
 * Library section component for sidebar.
 *
 * Displays library navigation items (Home, Authors, Series, etc.).
 * Follows SRP by handling only library section rendering.
 * Follows IOC by accepting all behavior via props.
 *
 * Parameters
 * ----------
 * props : LibrarySectionProps
 *     Component props.
 */
export function LibrarySection({
  isCollapsed,
  isExpanded,
  onToggle,
  onHomeClick,
}: LibrarySectionProps) {
  return (
    <SidebarSection
      title="MY LIBRARY"
      icon={LibraryBuilding}
      isCollapsed={isCollapsed}
      isExpanded={isExpanded}
      onToggle={onToggle}
    >
      <SidebarNavItem label="Home" onClick={onHomeClick} />
      <SidebarNavItem label="Authors" onClick={() => {}} />
      <SidebarNavItem label="Series" onClick={() => {}} />
      <SidebarNavItem label="Genres" onClick={() => {}} />
      <SidebarNavItem label="Publishers" onClick={() => {}} />
    </SidebarSection>
  );
}
