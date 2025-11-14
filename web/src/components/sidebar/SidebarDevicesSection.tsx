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

import { StatusPill } from "@/components/common/StatusPill";
import type { EReaderDevice } from "@/contexts/UserContext";
import { SharpDevicesFold } from "@/icons/SharpDevicesFold";
import { getDeviceDisplayName } from "@/utils/devices";
import { SidebarNavItem } from "./SidebarNavItem";
import { SidebarSection } from "./SidebarSection";

export interface SidebarDevicesSectionProps {
  /** Whether the sidebar is collapsed. */
  isCollapsed: boolean;
  /** Whether the section is expanded. */
  isExpanded: boolean;
  /** Callback when section header is clicked. */
  onToggle: () => void;
  /** List of devices to display. */
  devices: EReaderDevice[];
  /** Callback when a device is clicked. */
  onDeviceClick: (deviceId: number) => void;
  /** Callback when manage devices is clicked. */
  onManageDevicesClick: () => void;
}

/**
 * Devices section component for sidebar.
 *
 * Displays recent devices and manage devices link.
 * Follows SRP by handling only devices section rendering.
 * Follows IOC by accepting all behavior via props.
 *
 * Parameters
 * ----------
 * props : SidebarDevicesSectionProps
 *     Component props.
 */
export function SidebarDevicesSection({
  isCollapsed,
  isExpanded,
  onToggle,
  devices,
  onDeviceClick,
  onManageDevicesClick,
}: SidebarDevicesSectionProps) {
  return (
    <SidebarSection
      title="DEVICES"
      icon={SharpDevicesFold}
      isCollapsed={isCollapsed}
      isExpanded={isExpanded}
      onToggle={onToggle}
    >
      {devices.length === 0 ? (
        <li className="px-[46px] py-2.5 text-[var(--color-text-a30)] text-sm">
          No devices yet
        </li>
      ) : (
        devices.map((device) => (
          <SidebarNavItem
            key={device.id}
            label={getDeviceDisplayName(device)}
            onClick={() => onDeviceClick(device.id)}
          >
            {device.is_default && (
              <StatusPill
                label="Default"
                variant="info"
                icon="pi pi-info-circle"
                size="tiny"
              />
            )}
          </SidebarNavItem>
        ))
      )}
      <SidebarNavItem label="Manage devices" onClick={onManageDevicesClick} />
    </SidebarSection>
  );
}
