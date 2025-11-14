import { describe, expect, it } from "vitest";
import { isValidEmail, validateEmail } from "./validation";

describe("validation utils", () => {
  describe("isValidEmail", () => {
    it.each([
      { email: "test@example.com", expected: true },
      { email: "user.name@example.co.uk", expected: true },
      { email: "user+tag@example.com", expected: true },
      { email: "user123@example-domain.com", expected: true },
      { email: "a@b.co", expected: true },
      { email: "  test@example.com  ", expected: true }, // trimmed
      { email: "invalid", expected: false },
      { email: "invalid@", expected: false },
      { email: "@example.com", expected: false },
      { email: "test@", expected: false },
      { email: "test @example.com", expected: false },
      { email: "", expected: false },
      { email: "   ", expected: false }, // trimmed to empty
    ])("should return $expected for email '$email'", ({ email, expected }) => {
      expect(isValidEmail(email)).toBe(expected);
    });
  });

  describe("validateEmail", () => {
    it("should return undefined for valid email", () => {
      expect(validateEmail("test@example.com")).toBeUndefined();
    });

    it("should return error for empty email", () => {
      expect(validateEmail("")).toBe("Email is required.");
    });

    it("should return error for whitespace-only email", () => {
      expect(validateEmail("   ")).toBe("Email is required.");
    });

    it("should return error for invalid email format", () => {
      expect(validateEmail("invalid")).toBe(
        "Please enter a valid email address.",
      );
    });

    it("should trim email before validation", () => {
      expect(validateEmail("  test@example.com  ")).toBeUndefined();
      expect(validateEmail("  invalid  ")).toBe(
        "Please enter a valid email address.",
      );
    });

    it("should return error for email with spaces", () => {
      expect(validateEmail("test @example.com")).toBe(
        "Please enter a valid email address.",
      );
    });

    it("should return error for email without domain", () => {
      expect(validateEmail("test@")).toBe(
        "Please enter a valid email address.",
      );
    });

    it("should return error for email without @", () => {
      expect(validateEmail("testexample.com")).toBe(
        "Please enter a valid email address.",
      );
    });
  });
});
