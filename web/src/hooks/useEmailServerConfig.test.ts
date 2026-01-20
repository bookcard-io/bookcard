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

import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { EmailServerConfigData } from "@/services/emailServerConfigService";
import { useEmailServerConfig } from "./useEmailServerConfig";

vi.mock("@/services/emailServerConfigService", () => ({
  fetchEmailServerConfig: vi.fn(),
  updateEmailServerConfig: vi.fn(),
}));

import * as emailServerConfigService from "@/services/emailServerConfigService";

/**
 * Creates a mock email server config.
 *
 * Parameters
 * ----------
 * overrides : Partial<EmailServerConfigData>
 *     Optional overrides for default values.
 *
 * Returns
 * -------
 * EmailServerConfigData
 *     Mock email server config.
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

describe("useEmailServerConfig", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Set default mock implementation
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(createMockConfig());
  });

  it("should initialize with default form data", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.formData.server_type).toBe("smtp");
    expect(result.current.formData.smtp_port).toBe(587);
    expect(result.current.formData.smtp_use_tls).toBe(true);
    expect(result.current.formData.smtp_use_ssl).toBe(false);
    expect(result.current.formData.max_email_size_mb).toBe(25);
    expect(result.current.formData.enabled).toBe(true);
  });

  it("should load configuration on mount", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.config).toEqual(mockConfig);
    expect(result.current.hasChanges).toBe(false);
  });

  it("should handle field changes", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("smtp_host", "new.host.com");
    });

    expect(result.current.formData.smtp_host).toBe("new.host.com");
    expect(result.current.error).toBeNull();
  });

  it("should handle server type change", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleServerTypeChange("gmail");
    });

    expect(result.current.formData.server_type).toBe("gmail");
  });

  it("should detect changes when form data differs from config", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("smtp_host", "different.host.com");
    });

    await waitFor(() => {
      expect(result.current.hasChanges).toBe(true);
    });
  });

  it("should detect password changes", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("smtp_password", "newpassword");
    });

    await waitFor(() => {
      expect(result.current.hasChanges).toBe(true);
    });
  });

  it("should handle cancel and reset form data", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("smtp_host", "changed.host.com");
    });

    await waitFor(() => {
      expect(result.current.hasChanges).toBe(true);
    });

    act(() => {
      result.current.handleCancel();
    });

    expect(result.current.formData.smtp_host).toBe(mockConfig.smtp_host);
    expect(result.current.hasChanges).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("should submit SMTP configuration successfully", async () => {
    const mockConfig = createMockConfig();
    const updatedConfig = createMockConfig({ smtp_host: "updated.host.com" });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockResolvedValue(updatedConfig);

    const mockOnSaveSuccess = vi.fn();
    const { result } = renderHook(() =>
      useEmailServerConfig({ onSaveSuccess: mockOnSaveSuccess }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("smtp_host", "updated.host.com");
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(
      vi.mocked(emailServerConfigService.updateEmailServerConfig),
    ).toHaveBeenCalled();
    expect(result.current.config).toEqual(updatedConfig);
    expect(result.current.formData.smtp_password).toBe("**********");
    expect(result.current.hasChanges).toBe(false);
    expect(mockOnSaveSuccess).toHaveBeenCalledWith(updatedConfig);
  });

  it("should submit Gmail configuration successfully", async () => {
    const mockConfig = createMockConfig({ server_type: "gmail" });
    const updatedConfig = createMockConfig({
      server_type: "gmail",
      gmail_token: { token: "test-token" },
    });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockResolvedValue(updatedConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("gmail_token", { token: "test-token" });
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(
      vi.mocked(emailServerConfigService.updateEmailServerConfig),
    ).toHaveBeenCalled();
    expect(result.current.config).toEqual(updatedConfig);
  });

  it("should handle submit error", async () => {
    const mockConfig = createMockConfig();
    const error = new Error("Save failed");
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockRejectedValue(error);

    const mockOnError = vi.fn();
    const { result } = renderHook(() =>
      useEmailServerConfig({ onError: mockOnError }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(result.current.error).toBe("Save failed");
    expect(mockOnError).toHaveBeenCalledWith("Save failed");
  });

  it("should handle load error", async () => {
    const error = new Error("Load failed");
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockRejectedValue(error);

    const mockOnError = vi.fn();
    const { result } = renderHook(() =>
      useEmailServerConfig({ onError: mockOnError }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Load failed");
    expect(mockOnError).toHaveBeenCalledWith("Load failed");
  });

  it("should handle load error with non-Error object", async () => {
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockRejectedValue("String error");

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to load configuration");
  });

  it("should include SMTP fields in payload when server_type is smtp", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("smtp_host", "test.host.com");
      result.current.handleFieldChange("smtp_port", 465);
      result.current.handleFieldChange("smtp_username", "user");
      result.current.handleFieldChange("smtp_password", "pass");
      result.current.handleFieldChange("smtp_use_tls", false);
      result.current.handleFieldChange("smtp_use_ssl", true);
      result.current.handleFieldChange("smtp_from_email", "from@test.com");
      result.current.handleFieldChange("smtp_from_name", "Test");
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(
      vi.mocked(emailServerConfigService.updateEmailServerConfig),
    ).toHaveBeenCalledWith(
      expect.objectContaining({
        server_type: "smtp",
        smtp_host: "test.host.com",
        smtp_port: 465,
        smtp_username: "user",
        smtp_password: "pass",
        smtp_use_tls: false,
        smtp_use_ssl: true,
        smtp_from_email: "from@test.com",
        smtp_from_name: "Test",
      }),
    );
  });

  it("should include Gmail fields in payload when server_type is gmail", async () => {
    const mockConfig = createMockConfig({ server_type: "gmail" });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("gmail_token", { token: "token" });
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(
      vi.mocked(emailServerConfigService.updateEmailServerConfig),
    ).toHaveBeenCalledWith(
      expect.objectContaining({
        server_type: "gmail",
        gmail_token: { token: "token" },
      }),
    );
  });

  it("should set isSaving during submit", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    let resolveUpdate: (value: EmailServerConfigData) => void;
    const updatePromise = new Promise<EmailServerConfigData>((resolve) => {
      resolveUpdate = resolve;
    });
    vi.mocked(emailServerConfigService.updateEmailServerConfig).mockReturnValue(
      updatePromise,
    );

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Start submit but don't await it yet
    act(() => {
      void result.current.handleSubmit();
    });

    // Check isSaving is true immediately
    await waitFor(() => {
      expect(result.current.isSaving).toBe(true);
    });

    // Resolve the promise
    act(() => {
      resolveUpdate?.(mockConfig);
    });

    // Wait for isSaving to become false
    await waitFor(() => {
      expect(result.current.isSaving).toBe(false);
    });
  });

  it("should initialize form data with null values correctly", async () => {
    const mockConfig = createMockConfig({
      smtp_host: null,
      smtp_username: null,
      smtp_from_email: null,
      smtp_from_name: null,
    });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(
      () => {
        expect(result.current.isLoading).toBe(false);
      },
      { timeout: 3000 },
    );

    expect(result.current.formData.smtp_host).toBeNull();
    expect(result.current.formData.smtp_username).toBeNull();
    expect(result.current.formData.smtp_from_email).toBeNull();
    expect(result.current.formData.smtp_from_name).toBeNull();
  });

  it("should not detect changes when form data matches config", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasChanges).toBe(false);
  });

  it("should include optional SMTP fields in payload when provided", async () => {
    const mockConfig = createMockConfig({
      smtp_host: null,
      smtp_port: undefined,
      smtp_username: null,
    });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("smtp_host", "test.host.com");
      result.current.handleFieldChange("smtp_port", 465);
      result.current.handleFieldChange("smtp_username", "user");
      result.current.handleFieldChange("smtp_password", "pass");
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    // Should include fields when they are provided (lines 209-212)
    expect(
      vi.mocked(emailServerConfigService.updateEmailServerConfig),
    ).toHaveBeenCalledWith(
      expect.objectContaining({
        smtp_host: "test.host.com",
        smtp_port: 465,
        smtp_username: "user",
        smtp_password: "pass",
      }),
    );
  });

  it("should include optional SMTP TLS/SSL and from fields in payload when provided", async () => {
    const mockConfig = createMockConfig({
      smtp_use_tls: undefined,
      smtp_use_ssl: undefined,
      smtp_from_email: null,
      smtp_from_name: null,
    });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("smtp_use_tls", false);
      result.current.handleFieldChange("smtp_use_ssl", true);
      result.current.handleFieldChange("smtp_from_email", "from@test.com");
      result.current.handleFieldChange("smtp_from_name", "Test Name");
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    // Should include fields when they are provided (lines 217-225)
    expect(
      vi.mocked(emailServerConfigService.updateEmailServerConfig),
    ).toHaveBeenCalledWith(
      expect.objectContaining({
        smtp_use_tls: false,
        smtp_use_ssl: true,
        smtp_from_email: "from@test.com",
        smtp_from_name: "Test Name",
      }),
    );
  });

  it("should include Gmail token in payload when provided", async () => {
    const mockConfig = createMockConfig({ server_type: "gmail" });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("gmail_token", { token: "token123" });
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    // Should include gmail_token when provided (line 231)
    expect(
      vi.mocked(emailServerConfigService.updateEmailServerConfig),
    ).toHaveBeenCalledWith(
      expect.objectContaining({
        server_type: "gmail",
        gmail_token: { token: "token123" },
      }),
    );
  });

  it("should handle submit error with non-Error object", async () => {
    const mockConfig = createMockConfig();
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockRejectedValue("String error");

    const mockOnError = vi.fn();
    const { result } = renderHook(() =>
      useEmailServerConfig({ onError: mockOnError }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    // Should handle non-Error object (lines 247-249)
    expect(result.current.error).toBe("Failed to save configuration");
    expect(mockOnError).toHaveBeenCalledWith("Failed to save configuration");
  });

  it("should initialize password field with placeholder if has_smtp_password is true", async () => {
    const mockConfig = createMockConfig({ has_smtp_password: true });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.formData.smtp_password).toBe("**********");
  });

  it("should initialize password field as undefined if has_smtp_password is false", async () => {
    const mockConfig = createMockConfig({ has_smtp_password: false });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.formData.smtp_password).toBeUndefined();
  });

  it("should not send password if it is the placeholder value", async () => {
    const mockConfig = createMockConfig({ has_smtp_password: true });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Ensure it's set to placeholder
    expect(result.current.formData.smtp_password).toBe("**********");

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(
      vi.mocked(emailServerConfigService.updateEmailServerConfig),
    ).toHaveBeenCalledWith(
      expect.objectContaining({
        server_type: "smtp",
      }),
    );
    // Should NOT have smtp_password in the call args
    const mockCalls = vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mock.calls;
    expect(mockCalls[0]).toBeDefined();
    const callArgs = mockCalls[0]?.[0];
    expect(callArgs?.smtp_password).toBeUndefined();
  });

  it("should send password if it is cleared (empty string)", async () => {
    const mockConfig = createMockConfig({ has_smtp_password: true });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);
    vi.mocked(
      emailServerConfigService.updateEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFieldChange("smtp_password", "");
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(
      vi.mocked(emailServerConfigService.updateEmailServerConfig),
    ).toHaveBeenCalledWith(
      expect.objectContaining({
        smtp_password: "",
      }),
    );
  });

  it("should not detect changes if password field is touched but left empty when no password exists", async () => {
    const mockConfig = createMockConfig({ has_smtp_password: false });
    vi.mocked(
      emailServerConfigService.fetchEmailServerConfig,
    ).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useEmailServerConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      // Simulate user typing then clearing, or just focusing and leaving empty
      result.current.handleFieldChange("smtp_password", "");
    });

    await waitFor(() => {
      // Should NOT be considered a change because no password existed
      expect(result.current.hasChanges).toBe(false);
    });
  });
});
