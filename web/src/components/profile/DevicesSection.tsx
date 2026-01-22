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
import {
  getFormatLabel,
  SUPPORTED_BOOK_FORMAT_EXTENSIONS,
} from "@/constants/bookFormats";
import { useUser } from "@/contexts/UserContext";
import { cn } from "@/libs/utils";
import {
  createDevice,
  deleteDevice,
  updateDevice,
} from "@/services/deviceService";
import { AddDeviceCard } from "./AddDeviceCard";
import { DeviceCard } from "./DeviceCard";
import { DeviceEditModal } from "./DeviceEditModal";
import type { EReaderDevice } from "./hooks/useUserProfile";

interface DevicesSectionProps {
  devices: EReaderDevice[] | undefined;
}

const SEND_FORMAT_PRIORITY_SETTING_KEY = "send_format_priority";

// A simple, opinionated "most popular first" list; the rest are appended
// in backend-consistent supported format order.
const POPULAR_SEND_FORMATS: readonly string[] = [
  "epub",
  "pdf",
  "azw3",
  "mobi",
  "kepub",
  "azw",
  "cbz",
  "cbr",
  "djvu",
  "docx",
  "fb2",
  "rtf",
  "txt",
] as const;

type DropSide = "before" | "after";

function moveToInsertionIndex<T>(
  items: T[],
  fromIndex: number,
  insertionIndex: number,
): T[] {
  const next = items.slice();
  const [moved] = next.splice(fromIndex, 1);
  if (moved === undefined) {
    return items;
  }

  // insertionIndex refers to the "slot" in the original list. After removal,
  // everything to the right shifts left by one.
  let targetIndex = insertionIndex;
  if (fromIndex < targetIndex) {
    targetIndex -= 1;
  }
  targetIndex = Math.max(0, Math.min(targetIndex, next.length));

  next.splice(targetIndex, 0, moved);
  return next;
}

function getDropSideFromEventTarget(
  el: HTMLElement,
  clientX: number,
): DropSide {
  const rect = el.getBoundingClientRect();
  const mid = rect.left + rect.width / 2;
  return clientX < mid ? "before" : "after";
}

function buildDefaultSendFormatPriority(): string[] {
  const popularSet = new Set(POPULAR_SEND_FORMATS);
  const popular = POPULAR_SEND_FORMATS.filter((f) =>
    SUPPORTED_BOOK_FORMAT_EXTENSIONS.includes(f as never),
  );
  const remaining = SUPPORTED_BOOK_FORMAT_EXTENSIONS.filter(
    (f) => !popularSet.has(f),
  );
  return [...popular, ...remaining];
}

function normalizeSendFormatPriority(value: string | null): string[] {
  const supported =
    SUPPORTED_BOOK_FORMAT_EXTENSIONS.slice() as unknown as string[];
  const supportedSet = new Set(supported.map((f) => f.toLowerCase()));

  if (!value) {
    return buildDefaultSendFormatPriority();
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(value);
  } catch {
    // Backward-compatible: comma-separated list
    parsed = value.split(",").map((s) => s.trim());
  }

  const rawList = Array.isArray(parsed) ? parsed : [];
  const cleaned: string[] = [];
  const seen = new Set<string>();

  for (const item of rawList) {
    if (typeof item !== "string") {
      continue;
    }
    const normalized = item.trim().toLowerCase();
    if (!normalized || !supportedSet.has(normalized) || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    cleaned.push(normalized);
  }

  // Always include all supported formats (append any missing)
  for (const f of supported) {
    const normalized = f.toLowerCase();
    if (!seen.has(normalized)) {
      cleaned.push(normalized);
      seen.add(normalized);
    }
  }

  return cleaned.length > 0 ? cleaned : buildDefaultSendFormatPriority();
}

/**
 * Devices section displaying user's e-reader devices.
 *
 * Shows a grid of device cards with ability to manage them (no-op for now).
 * Follows SRP by handling only device display and management UI.
 * Follows DRY by reusing ShelvesGrid layout pattern.
 */
export function DevicesSection({ devices }: DevicesSectionProps) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingDevice, setEditingDevice] = useState<EReaderDevice | null>(
    null,
  );
  const { refresh, updateUser, user, getSetting, updateSetting, isSaving } =
    useUser();

  const deviceList = devices || [];

  const [sendFormatPriority, setSendFormatPriority] = useState<string[]>(() =>
    normalizeSendFormatPriority(getSetting(SEND_FORMAT_PRIORITY_SETTING_KEY)),
  );
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dropIndicator, setDropIndicator] = useState<{
    index: number;
    side: DropSide;
  } | null>(null);

  const handleCreateDevice = async (data: {
    email: string;
    device_name?: string | null;
    device_type?: string;
    preferred_format?: string | null;
    is_default?: boolean;
  }) => {
    const newDevice = await createDevice(data);

    // Optimistically update devices in user context.
    // If the new device is default, clear the default flag on all others
    // so only one card shows the asterisk immediately.
    const isNewDefault = Boolean(data.is_default);

    if (user) {
      const existingDevices = user.ereader_devices ?? [];

      const normalizedNewDevice: EReaderDevice = {
        ...newDevice,
        // Ensure the new device reflects the default choice immediately
        is_default: isNewDefault ? true : newDevice.is_default,
      };

      const clearedDefaults = isNewDefault
        ? existingDevices.map((device) => ({
            ...device,
            is_default: false,
          }))
        : existingDevices;

      const updatedDevices = [...clearedDefaults, normalizedNewDevice];
      updateUser({ ereader_devices: updatedDevices });
    }

    // UI already updated optimistically, no need to refresh
    return newDevice;
  };

  const handleUpdateDevice = async (data: {
    email: string;
    device_name?: string | null;
    device_type?: string;
    preferred_format?: string | null;
    is_default?: boolean;
  }) => {
    if (!editingDevice) {
      throw new Error("No device to update");
    }

    const updatedDevice = await updateDevice(editingDevice.id, data);

    // Optimistically update device in user context
    const isNewDefault = Boolean(data.is_default);

    if (user) {
      const existingDevices = user.ereader_devices ?? [];

      const normalizedUpdatedDevice: EReaderDevice = {
        ...updatedDevice,
        is_default: isNewDefault ? true : updatedDevice.is_default,
      };

      // If setting as default, clear default flag on all other devices
      const clearedDefaults = isNewDefault
        ? existingDevices.map((device) =>
            device.id === editingDevice.id
              ? normalizedUpdatedDevice
              : { ...device, is_default: false },
          )
        : existingDevices.map((device) =>
            device.id === editingDevice.id ? normalizedUpdatedDevice : device,
          );

      updateUser({ ereader_devices: clearedDefaults });
    }

    return updatedDevice;
  };

  const handleDeleteDevice = async (deviceId: number) => {
    // Optimistically remove device from UI immediately
    if (user?.ereader_devices) {
      const updatedDevices = user.ereader_devices.filter(
        (d) => d.id !== deviceId,
      );
      updateUser({ ereader_devices: updatedDevices });
    }

    try {
      await deleteDevice(deviceId);
      // UI already updated optimistically, no need to refresh
    } catch (error) {
      // On error, revert by refreshing from server
      await refresh();
      throw error;
    }
  };

  return (
    <div id="manage-devices" className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2
          className={cn(
            /* Layout */
            "m-0",
            /* Typography */
            "font-semibold text-text-a0 text-xl",
          )}
        >
          My Devices
        </h2>
      </div>
      <p className="text-sm text-text-a60">
        Devices are used for sending books via email (e.g., Send to Kindle). You
        can add multiple devices and set a default. All send-to and email
        features require a device with an email address.
      </p>

      <div className="w-full">
        {deviceList.length > 0 && (
          <div className="pb-4 text-left text-sm text-text-a40">
            {deviceList.length} {deviceList.length === 1 ? "device" : "devices"}
          </div>
        )}
        <div
          className={cn(
            /* Layout */
            "grid justify-items-start gap-4",
            /* Grid columns */
            "grid-cols-[repeat(auto-fit,minmax(110px,175px))]",
            "md:grid-cols-[repeat(auto-fit,minmax(110px,175px))] md:gap-4",
            "lg:grid-cols-[repeat(auto-fit,minmax(110px,175px))]",
          )}
        >
          {deviceList.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              onEdit={(device) => setEditingDevice(device)}
              onDelete={handleDeleteDevice}
            />
          ))}
          {/* Always show "Add device" card as the last item */}
          <AddDeviceCard onClick={() => setShowAddModal(true)} />
        </div>
      </div>

      {deviceList.length > 0 && (
        <div className="rounded-lg border border-[var(--color-surface-a20)] p-4">
          <div className="flex items-center gap-2">
            <h3 className="m-0 font-semibold text-base text-text-a0">
              Send format priority
            </h3>
            {isSaving && (
              <div className="flex items-center gap-2 text-sm text-text-a30">
                <i className="pi pi-spin pi-spinner" aria-hidden="true" />
                <span>Saving...</span>
              </div>
            )}
          </div>
          <p className="mt-2 text-sm text-text-a60">
            Drag to reorder. When sending a book without an explicit format,
            we’ll pick the first available format based on this order.
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {sendFormatPriority.map((format, index) => (
              <div key={format} className="relative inline-flex">
                {dropIndicator?.index === index &&
                  dropIndicator.side === "before" && (
                    <span
                      className={cn(
                        "-translate-y-1/2 pointer-events-none absolute top-1/2 left-[-6px] h-6 w-px",
                        "bg-[var(--color-primary-a0)]",
                      )}
                      aria-hidden="true"
                    />
                  )}
                {dropIndicator?.index === index &&
                  dropIndicator.side === "after" && (
                    <span
                      className={cn(
                        "-translate-y-1/2 pointer-events-none absolute top-1/2 right-[-6px] h-6 w-px",
                        "bg-[var(--color-primary-a0)]",
                      )}
                      aria-hidden="true"
                    />
                  )}

                <button
                  type="button"
                  draggable
                  onDragStart={(e) => {
                    // Some browsers won't start drag unless data is set.
                    e.dataTransfer?.setData("text/plain", format);
                    setDragIndex(index);
                    setDropIndicator(null);
                  }}
                  onDragEnd={() => {
                    setDragIndex(null);
                    setDropIndicator(null);
                  }}
                  onDragLeave={() => {
                    // Keep the indicator stable when moving between pills; clear only
                    // if we're leaving the currently-indicated target.
                    if (dropIndicator?.index === index) {
                      setDropIndicator(null);
                    }
                  }}
                  onDragOver={(e) => {
                    e.preventDefault();
                    if (dragIndex === null || dragIndex === index) {
                      setDropIndicator(null);
                      return;
                    }
                    const side = getDropSideFromEventTarget(
                      e.currentTarget,
                      e.clientX,
                    );
                    setDropIndicator({ index, side });
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (dragIndex === null) {
                      return;
                    }

                    const side = getDropSideFromEventTarget(
                      e.currentTarget,
                      e.clientX,
                    );
                    const insertionIndex = index + (side === "after" ? 1 : 0);
                    const next =
                      dragIndex === index
                        ? sendFormatPriority
                        : moveToInsertionIndex(
                            sendFormatPriority,
                            dragIndex,
                            insertionIndex,
                          );

                    setSendFormatPriority(next);
                    updateSetting(
                      SEND_FORMAT_PRIORITY_SETTING_KEY,
                      JSON.stringify(next),
                    );
                    setDragIndex(null);
                    setDropIndicator(null);
                  }}
                  className={cn(
                    "cursor-grab select-none rounded-full border px-3 py-1 text-sm",
                    "border-[var(--color-surface-a20)] bg-[var(--color-surface-a0)] text-text-a10",
                    dragIndex === index && "opacity-60",
                  )}
                  title="Drag to reorder"
                  aria-label={`Format ${getFormatLabel(format)}, drag to reorder`}
                >
                  {getFormatLabel(format)}
                </button>
              </div>
            ))}
          </div>

          <div className="mt-3 flex items-center justify-end">
            <button
              type="button"
              className={cn(
                "rounded-md border px-3 py-1.5 text-sm",
                "border-[var(--color-surface-a20)] text-text-a20 hover:text-text-a10",
              )}
              onClick={() => {
                const next = buildDefaultSendFormatPriority();
                setSendFormatPriority(next);
                updateSetting(
                  SEND_FORMAT_PRIORITY_SETTING_KEY,
                  JSON.stringify(next),
                );
              }}
            >
              Reset to default
            </button>
          </div>
        </div>
      )}
      {showAddModal && (
        <DeviceEditModal
          onClose={() => setShowAddModal(false)}
          onSave={handleCreateDevice}
        />
      )}
      {editingDevice && (
        <DeviceEditModal
          device={editingDevice}
          onClose={() => setEditingDevice(null)}
          onSave={handleUpdateDevice}
        />
      )}
    </div>
  );
}
