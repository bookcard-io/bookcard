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

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  type EmailServerConfigData,
  type EmailServerConfigUpdate,
  fetchEmailServerConfig,
  updateEmailServerConfig,
} from "./emailServerConfigService";

/**
 * Creates a mock fetch response.
 *
 * Parameters
 * ----------
 * ok : boolean
 *     Response ok status.
 * jsonData : unknown
 *     JSON data to return.
 * jsonError : Error | null
 *     Optional error to throw from json().
 *
 * Returns
 * -------
 * Response
 *     Mock response object.
 */
function createMockResponse(
  ok: boolean,
  jsonData: unknown = {},
  jsonError: Error | null = null,
) {
  return {
    ok,
    json: jsonError
      ? vi.fn().mockRejectedValue(jsonError)
      : vi.fn().mockResolvedValue(jsonData),
  };
}

/**
 * Creates a mock email server config data.
 *
 * Parameters
 * ----------
 * overrides : Partial<EmailServerConfigData>
 *     Optional overrides for default values.
 *
 * Returns
 * -------
 * EmailServerConfigData
 *     Mock email server config data.
 */
function createMockConfig(
  overrides: Partial<EmailServerConfigData> = {},
): EmailServerConfigData {
  return {
    id: 1,
    server_type: "smtp",
    smtp_host: "smtp.example.com",
    smtp_port: 587,
    smtp_username: "user@example.com",
    smtp_use_tls: true,
    smtp_use_ssl: false,
    smtp_from_email: "from@example.com",
    smtp_from_name: "Test Sender",
    has_smtp_password: true,
    max_email_size_mb: 25,
    gmail_token: null,
    enabled: true,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("emailServerConfigService", () => {
  const apiBase = "/api/auth/email-server-config";
  const baseHeaders = {
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchEmailServerConfig", () => {
    it("should fetch email server config successfully", async () => {
      const mockConfig = createMockConfig();
      const mockResponse = createMockResponse(true, mockConfig);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await fetchEmailServerConfig();

      expect(globalThis.fetch).toHaveBeenCalledWith(apiBase, {
        method: "GET",
        headers: baseHeaders,
        credentials: "include",
      });
      expect(result).toEqual(mockConfig);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Unauthorized" },
        "Unauthorized",
      ],
      [
        "without detail in error response",
        {},
        "Failed to fetch email server config",
      ],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to fetch email server config",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(fetchEmailServerConfig()).rejects.toThrow(expectedMessage);
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(fetchEmailServerConfig()).rejects.toThrow(
        "Failed to fetch email server config",
      );
    });
  });

  describe("updateEmailServerConfig", () => {
    it("should update email server config successfully", async () => {
      const updateData: EmailServerConfigUpdate = {
        server_type: "gmail",
        smtp_host: "smtp.gmail.com",
        enabled: true,
      };
      const mockConfig = createMockConfig(updateData);
      const mockResponse = createMockResponse(true, mockConfig);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await updateEmailServerConfig(updateData);

      expect(globalThis.fetch).toHaveBeenCalledWith(apiBase, {
        method: "PUT",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(updateData),
      });
      expect(result).toEqual(mockConfig);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Validation error" },
        "Validation error",
      ],
      [
        "without detail in error response",
        {},
        "Failed to update email server config",
      ],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to update email server config",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const updateData: EmailServerConfigUpdate = { enabled: false };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateEmailServerConfig(updateData)).rejects.toThrow(
        expectedMessage,
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const updateData: EmailServerConfigUpdate = { enabled: true };
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateEmailServerConfig(updateData)).rejects.toThrow(
        "Failed to update email server config",
      );
    });
  });
});
