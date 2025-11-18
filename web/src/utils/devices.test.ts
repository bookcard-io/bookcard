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

import { describe, expect, it } from "vitest";
import type { EReaderDevice } from "@/contexts/UserContext";
import { getDeviceDisplayName } from "./devices";

describe("getDeviceDisplayName", () => {
  it("should return device_name when available", () => {
    const device: EReaderDevice = {
      id: 1,
      user_id: 1,
      email: "device@example.com",
      device_name: "My Kindle",
      device_type: "kindle",
      preferred_format: "mobi",
      is_default: false,
    };

    expect(getDeviceDisplayName(device)).toBe("My Kindle");
  });

  it("should return email when device_name is null", () => {
    const device: EReaderDevice = {
      id: 1,
      user_id: 1,
      email: "device@example.com",
      device_name: null,
      device_type: "kindle",
      preferred_format: "mobi",
      is_default: false,
    };

    expect(getDeviceDisplayName(device)).toBe("device@example.com");
  });

  it("should return email when device_name is empty string", () => {
    const device: EReaderDevice = {
      id: 1,
      user_id: 1,
      email: "device@example.com",
      device_name: "",
      device_type: "kindle",
      preferred_format: "mobi",
      is_default: false,
    };

    expect(getDeviceDisplayName(device)).toBe("device@example.com");
  });
});
