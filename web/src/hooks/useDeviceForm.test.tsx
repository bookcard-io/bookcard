import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock dependencies - must be before imports
vi.mock("@/utils/device", () => ({
  generateDeviceName: vi.fn(() => "My Kindle"),
}));

vi.mock("@/utils/deviceErrors", () => ({
  isEmailError: vi.fn(() => false),
  translateDeviceError: vi.fn((error: string) => error),
}));

vi.mock("@/utils/validation", () => ({
  validateEmail: vi.fn(() => undefined),
}));

import type { DeviceCreate } from "@/components/profile/DeviceEditModal";
import type { EReaderDevice } from "@/components/profile/hooks/useUserProfile";
import type { EReaderDevice as ContextEReaderDevice } from "@/contexts/UserContext";
import { generateDeviceName } from "@/utils/device";
import { isEmailError, translateDeviceError } from "@/utils/deviceErrors";
import { validateEmail } from "@/utils/validation";
import { useDeviceForm } from "./useDeviceForm";

describe("useDeviceForm", () => {
  let mockOnSubmit: ReturnType<
    typeof vi.fn<(data: DeviceCreate) => Promise<EReaderDevice> | Promise<void>>
  >;
  let mockDevice: EReaderDevice;

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnSubmit = vi
      .fn<(data: DeviceCreate) => Promise<EReaderDevice> | Promise<void>>()
      .mockResolvedValue(undefined);
    mockDevice = {
      id: 1,
      user_id: 1,
      email: "test@example.com",
      device_name: "Test Device",
      device_type: "kindle",
      is_default: true,
      preferred_format: "epub",
    };
    // Reset mocks to default values
    vi.mocked(validateEmail).mockReset().mockReturnValue(undefined);
    vi.mocked(generateDeviceName).mockReset().mockReturnValue("My Kindle");
    vi.mocked(isEmailError).mockReset().mockReturnValue(false);
    vi.mocked(translateDeviceError)
      .mockReset()
      .mockImplementation((error) => error);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("initialization", () => {
    it("should initialize with empty values when no initialDevice", () => {
      const { result } = renderHook(() => useDeviceForm());

      expect(result.current.email).toBe("");
      expect(result.current.deviceName).toBe("");
      expect(result.current.deviceType).toBe("kindle");
      expect(result.current.preferredFormat).toBe("");
      expect(result.current.isDefault).toBe(false);
      expect(result.current.isSubmitting).toBe(false);
      expect(result.current.errors).toEqual({});
      expect(result.current.generalError).toBeNull();
    });

    it("should initialize with initialDevice values", () => {
      const { result } = renderHook(() =>
        useDeviceForm({ initialDevice: mockDevice }),
      );

      expect(result.current.email).toBe("test@example.com");
      expect(result.current.deviceName).toBe("Test Device");
      expect(result.current.deviceType).toBe("kindle");
      expect(result.current.preferredFormat).toBe("epub");
      expect(result.current.isDefault).toBe(true);
    });

    it("should handle null initialDevice", () => {
      const { result } = renderHook(() =>
        useDeviceForm({ initialDevice: null }),
      );

      expect(result.current.email).toBe("");
      expect(result.current.deviceName).toBe("");
    });
  });

  describe("state setters", () => {
    it("should update email", () => {
      const { result } = renderHook(() => useDeviceForm());

      act(() => {
        result.current.setEmail("new@example.com");
      });

      expect(result.current.email).toBe("new@example.com");
    });

    it("should update deviceName", () => {
      const { result } = renderHook(() => useDeviceForm());

      act(() => {
        result.current.setDeviceName("New Device");
      });

      expect(result.current.deviceName).toBe("New Device");
    });

    it("should update deviceType", () => {
      const { result } = renderHook(() => useDeviceForm());

      act(() => {
        result.current.setDeviceType("kobo");
      });

      expect(result.current.deviceType).toBe("kobo");
    });

    it("should update preferredFormat", () => {
      const { result } = renderHook(() => useDeviceForm());

      act(() => {
        result.current.setPreferredFormat("pdf");
      });

      expect(result.current.preferredFormat).toBe("pdf");
    });

    it("should update isDefault", () => {
      const { result } = renderHook(() => useDeviceForm());

      act(() => {
        result.current.setIsDefault(true);
      });

      expect(result.current.isDefault).toBe(true);
    });
  });

  describe("clearErrors", () => {
    it("should clear all errors", () => {
      const { result } = renderHook(() => useDeviceForm());

      act(() => {
        result.current.setEmail("invalid");
      });

      // Set errors manually (simulating validation)
      act(() => {
        (
          result.current as unknown as {
            errors: { email?: string };
            generalError: string | null;
          }
        ).errors = { email: "Invalid email" };
        (
          result.current as unknown as {
            errors: { email?: string };
            generalError: string | null;
          }
        ).generalError = "General error";
      });

      act(() => {
        result.current.clearErrors();
      });

      expect(result.current.errors).toEqual({});
      expect(result.current.generalError).toBeNull();
    });
  });

  describe("validation", () => {
    it("should return false when email is invalid", async () => {
      vi.mocked(validateEmail).mockReturnValue("Email is required.");

      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setEmail("");
      });

      const isValid = await act(async () => {
        return result.current.handleSubmit();
      });

      expect(isValid).toBe(false);
      expect(result.current.errors.email).toBe("Email is required.");
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it("should return true when validation passes", async () => {
      vi.mocked(validateEmail).mockReturnValue(undefined);

      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
      });

      const isValid = await act(async () => {
        return result.current.handleSubmit();
      });

      expect(isValid).toBe(true);
      expect(result.current.errors).toEqual({});
      expect(mockOnSubmit).toHaveBeenCalled();
    });
  });

  describe("handleSubmit", () => {
    it("should submit form with provided values", async () => {
      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
        result.current.setDeviceName("My Device");
        result.current.setDeviceType("kobo");
        result.current.setPreferredFormat("pdf");
        result.current.setIsDefault(true);
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(mockOnSubmit).toHaveBeenCalledWith({
        email: "test@example.com",
        device_name: "My Device",
        device_type: "kobo",
        preferred_format: "pdf",
        is_default: true,
        serial_number: null,
      });
    });

    it("should include serial_number even when it is the last field edited", async () => {
      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
      });

      // Serial number is edited after email, and no other fields change before submit.
      // This guards against stale-closure bugs in handleSubmit dependencies.
      act(() => {
        result.current.setSerialNumber("  B001234  ");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          serial_number: "B001234",
        }),
      );
    });

    it("should trim email and preferredFormat", async () => {
      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setEmail("  test@example.com  ");
        result.current.setPreferredFormat("  epub  ");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          email: "test@example.com",
          preferred_format: "epub",
        }),
      );
    });

    it("should set preferredFormat to null when empty", async () => {
      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
        result.current.setPreferredFormat("");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          preferred_format: null,
        }),
      );
    });

    it("should generate device name when not provided in create mode", async () => {
      const existingDevices: ContextEReaderDevice[] = [];
      vi.mocked(generateDeviceName).mockReturnValue("My Kindle");

      const { result } = renderHook(() =>
        useDeviceForm({
          existingDevices,
          onSubmit: mockOnSubmit,
        }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
        result.current.setDeviceName(""); // Empty name
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(generateDeviceName).toHaveBeenCalledWith(existingDevices);
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          device_name: "My Kindle",
        }),
      );
    });

    it("should not generate device name in edit mode", async () => {
      const { result } = renderHook(() =>
        useDeviceForm({
          initialDevice: mockDevice,
          onSubmit: mockOnSubmit,
        }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
        result.current.setDeviceName(""); // Empty name in edit mode
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(generateDeviceName).not.toHaveBeenCalled();
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          device_name: null,
        }),
      );
    });

    it("should use trimmed device name when provided", async () => {
      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: mockOnSubmit }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
        result.current.setDeviceName("  My Device  ");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          device_name: "My Device",
        }),
      );
      expect(generateDeviceName).not.toHaveBeenCalled();
    });

    it("should set isSubmitting to false initially and after submission", async () => {
      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: mockOnSubmit }),
      );

      expect(result.current.isSubmitting).toBe(false);

      act(() => {
        result.current.setEmail("test@example.com");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      // isSubmitting should be false after submission completes
      expect(result.current.isSubmitting).toBe(false);
    });

    it("should handle submission error with Error instance", async () => {
      const error = new Error("Email already exists");
      const testOnSubmit = vi
        .fn<(data: DeviceCreate) => Promise<EReaderDevice> | Promise<void>>()
        .mockRejectedValue(error);
      const testOnError = vi.fn<(error: string) => void>();

      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: testOnSubmit, onError: testOnError }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(result.current.generalError).toBe("Email already exists");
      expect(testOnError).toHaveBeenCalledWith("Email already exists");
    });

    it("should handle submission error with non-Error value", async () => {
      const testOnSubmit = vi
        .fn<(data: DeviceCreate) => Promise<EReaderDevice> | Promise<void>>()
        .mockRejectedValue("String error");
      const testOnError = vi.fn<(error: string) => void>();

      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: testOnSubmit, onError: testOnError }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(result.current.generalError).toBe(
        "Failed to save device. Please try again.",
      );
      expect(testOnError).toHaveBeenCalledWith(
        "Failed to save device. Please try again.",
      );
    });

    it("should set email error when error is email-related", async () => {
      const error = new Error("device_email_already_exists");
      const testOnSubmit = vi
        .fn<(data: DeviceCreate) => Promise<EReaderDevice> | Promise<void>>()
        .mockRejectedValue(error);
      const testOnError = vi.fn<(error: string) => void>();
      vi.mocked(isEmailError).mockReturnValue(true);
      vi.mocked(translateDeviceError).mockReturnValue(
        "A device with this email already exists.",
      );

      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: testOnSubmit, onError: testOnError }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(result.current.errors.email).toBe(
        "A device with this email already exists.",
      );
      expect(result.current.generalError).toBeNull();
    });

    it("should not call onError when not provided", async () => {
      const error = new Error("Error");
      const testOnSubmit = vi
        .fn<(data: DeviceCreate) => Promise<EReaderDevice> | Promise<void>>()
        .mockRejectedValue(error);
      const testOnError = vi.fn<(error: string) => void>();

      const { result } = renderHook(() =>
        useDeviceForm({ onSubmit: testOnSubmit }),
      );

      act(() => {
        result.current.setEmail("test@example.com");
      });

      await act(async () => {
        await result.current.handleSubmit();
      });

      expect(testOnError).not.toHaveBeenCalled();
    });

    it("should not call onSubmit when not provided", async () => {
      const { result } = renderHook(() => useDeviceForm());

      act(() => {
        result.current.setEmail("test@example.com");
      });

      const isValid = await act(async () => {
        return result.current.handleSubmit();
      });

      expect(isValid).toBe(true);
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe("reset", () => {
    it("should reset to initial values when initialDevice is provided", () => {
      const { result } = renderHook(() =>
        useDeviceForm({ initialDevice: mockDevice }),
      );

      act(() => {
        result.current.setEmail("changed@example.com");
        result.current.setDeviceName("Changed Device");
        result.current.setDeviceType("kobo");
        result.current.setPreferredFormat("pdf");
        result.current.setIsDefault(false);
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.email).toBe("test@example.com");
      expect(result.current.deviceName).toBe("Test Device");
      expect(result.current.deviceType).toBe("kindle");
      expect(result.current.preferredFormat).toBe("epub");
      expect(result.current.isDefault).toBe(true);
      expect(result.current.errors).toEqual({});
      expect(result.current.generalError).toBeNull();
      expect(result.current.isSubmitting).toBe(false);
    });

    it("should reset to empty values when no initialDevice", () => {
      const { result } = renderHook(() => useDeviceForm());

      act(() => {
        result.current.setEmail("test@example.com");
        result.current.setDeviceName("Test Device");
        result.current.setIsDefault(true);
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.email).toBe("");
      expect(result.current.deviceName).toBe("");
      expect(result.current.deviceType).toBe("kindle");
      expect(result.current.preferredFormat).toBe("");
      expect(result.current.isDefault).toBe(false);
    });
  });

  it("should maintain stable handlers", () => {
    const { result, rerender } = renderHook(() => useDeviceForm());

    const initialSetEmail = result.current.setEmail;
    const initialSetDeviceName = result.current.setDeviceName;
    const initialSetDeviceType = result.current.setDeviceType;
    const initialSetPreferredFormat = result.current.setPreferredFormat;
    const initialSetIsDefault = result.current.setIsDefault;
    const initialClearErrors = result.current.clearErrors;
    const initialReset = result.current.reset;

    rerender();

    expect(result.current.setEmail).toBe(initialSetEmail);
    expect(result.current.setDeviceName).toBe(initialSetDeviceName);
    expect(result.current.setDeviceType).toBe(initialSetDeviceType);
    expect(result.current.setPreferredFormat).toBe(initialSetPreferredFormat);
    expect(result.current.setIsDefault).toBe(initialSetIsDefault);
    expect(result.current.clearErrors).toBe(initialClearErrors);
    // handleSubmit may not be stable due to dependencies (email, deviceName, etc.)
    // but other handlers should be stable
    expect(result.current.reset).toBe(initialReset);
  });
});
