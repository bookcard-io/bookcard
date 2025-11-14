import { describe, expect, it } from "vitest";
import {
  DeviceErrorCode,
  isEmailError,
  translateDeviceError,
} from "./deviceErrors";

describe("deviceErrors utils", () => {
  describe("DeviceErrorCode", () => {
    it("should have EMAIL_ALREADY_EXISTS constant", () => {
      expect(DeviceErrorCode.EMAIL_ALREADY_EXISTS).toBe(
        "device_email_already_exists",
      );
    });
  });

  describe("translateDeviceError", () => {
    it("should translate known error code", () => {
      const result = translateDeviceError(DeviceErrorCode.EMAIL_ALREADY_EXISTS);
      expect(result).toBe("A device with this email already exists.");
    });

    it("should return error code as-is for unknown error", () => {
      const unknownError = "unknown_error_code";
      const result = translateDeviceError(unknownError);
      expect(result).toBe(unknownError);
    });
  });

  describe("isEmailError", () => {
    it.each([
      { code: "device_email_already_exists", expected: true },
      { code: "email_invalid", expected: true },
      { code: "email_required", expected: true },
      { code: "some_email_error", expected: true },
      { code: "device_email_error", expected: true },
      { code: "other_error", expected: false },
      { code: "validation_failed", expected: false },
      { code: "", expected: false },
    ])(
      "should return $expected for error code '$code'",
      ({ code, expected }) => {
        expect(isEmailError(code)).toBe(expected);
      },
    );
  });
});
