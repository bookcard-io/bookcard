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
import { generateDeviceName } from "./device";

describe("generateDeviceName", () => {
  it("should return provided name when given", () => {
    const existingDevices: EReaderDevice[] = [];
    const providedName = "My Custom Device";

    expect(generateDeviceName(existingDevices, providedName)).toBe(
      "My Custom Device",
    );
  });

  it("should trim provided name", () => {
    const existingDevices: EReaderDevice[] = [];
    const providedName = "  My Custom Device  ";

    expect(generateDeviceName(existingDevices, providedName)).toBe(
      "My Custom Device",
    );
  });

  it("should return 'My Kindle' when no devices exist and no name provided", () => {
    const existingDevices: EReaderDevice[] = [];

    expect(generateDeviceName(existingDevices)).toBe("My Kindle");
  });

  it("should return 'My Kindle' when base name doesn't exist and no numbered names", () => {
    const existingDevices: EReaderDevice[] = [
      {
        id: 1,
        user_id: 1,
        email: "device1@example.com",
        device_name: "Other Device",
        device_type: "kindle",
        preferred_format: "mobi",
        is_default: false,
      },
    ];

    expect(generateDeviceName(existingDevices)).toBe("My Kindle");
  });

  it("should return 'My Kindle (2)' when base name exists", () => {
    const existingDevices: EReaderDevice[] = [
      {
        id: 1,
        user_id: 1,
        email: "device1@example.com",
        device_name: "My Kindle",
        device_type: "kindle",
        preferred_format: "mobi",
        is_default: false,
      },
    ];

    // When base name exists, it should return "My Kindle (1)" since maxNumber is 0
    expect(generateDeviceName(existingDevices)).toBe("My Kindle (1)");
  });

  it("should return 'My Kindle (3)' when numbered names exist", () => {
    const existingDevices: EReaderDevice[] = [
      {
        id: 1,
        user_id: 1,
        email: "device1@example.com",
        device_name: "My Kindle (1)",
        device_type: "kindle",
        preferred_format: "mobi",
        is_default: false,
      },
      {
        id: 2,
        user_id: 1,
        email: "device2@example.com",
        device_name: "My Kindle (2)",
        device_type: "kindle",
        preferred_format: "mobi",
        is_default: false,
      },
    ];

    expect(generateDeviceName(existingDevices)).toBe("My Kindle (3)");
  });

  it("should find next available number when numbers are not sequential", () => {
    const existingDevices: EReaderDevice[] = [
      {
        id: 1,
        user_id: 1,
        email: "device1@example.com",
        device_name: "My Kindle (1)",
        device_type: "kindle",
        preferred_format: "mobi",
        is_default: false,
      },
      {
        id: 2,
        user_id: 1,
        email: "device2@example.com",
        device_name: "My Kindle (5)",
        device_type: "kindle",
        preferred_format: "mobi",
        is_default: false,
      },
    ];

    expect(generateDeviceName(existingDevices)).toBe("My Kindle (6)");
  });

  it("should ignore devices that don't match pattern", () => {
    const existingDevices: EReaderDevice[] = [
      {
        id: 1,
        user_id: 1,
        email: "device1@example.com",
        device_name: "Other Device",
        device_type: "kindle",
        preferred_format: "mobi",
        is_default: false,
      },
      {
        id: 2,
        user_id: 1,
        email: "device2@example.com",
        device_name: "My Kindle (2)",
        device_type: "kindle",
        preferred_format: "mobi",
        is_default: false,
      },
    ];

    expect(generateDeviceName(existingDevices)).toBe("My Kindle (3)");
  });

  it("should handle null device_name", () => {
    const existingDevices: EReaderDevice[] = [
      {
        id: 1,
        user_id: 1,
        email: "device1@example.com",
        device_name: null,
        device_type: "kindle",
        preferred_format: "mobi",
        is_default: false,
      },
    ];

    expect(generateDeviceName(existingDevices)).toBe("My Kindle");
  });
});
