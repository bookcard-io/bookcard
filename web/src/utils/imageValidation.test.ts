import { describe, expect, it } from "vitest";
import {
  IMAGE_ACCEPT_ATTRIBUTE,
  isValidImageSize,
  isValidImageType,
  MAX_IMAGE_SIZE,
  VALID_IMAGE_TYPES,
  validateImageFile,
} from "./imageValidation";

describe("imageValidation utils", () => {
  describe("constants", () => {
    it("should have valid image types", () => {
      expect(VALID_IMAGE_TYPES).toEqual([
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
      ]);
    });

    it("should have max image size of 5MB", () => {
      expect(MAX_IMAGE_SIZE).toBe(5 * 1024 * 1024);
    });

    it("should have correct accept attribute", () => {
      expect(IMAGE_ACCEPT_ATTRIBUTE).toBe(
        "image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml",
      );
    });
  });

  describe("isValidImageType", () => {
    it.each([
      { type: "image/jpeg", expected: true },
      { type: "image/jpg", expected: true },
      { type: "image/png", expected: true },
      { type: "image/gif", expected: true },
      { type: "image/webp", expected: true },
      { type: "image/svg+xml", expected: true },
      { type: "image/bmp", expected: false },
      { type: "text/plain", expected: false },
      { type: "application/pdf", expected: false },
    ])("should return $expected for type '$type'", ({ type, expected }) => {
      const file = new File([], "test", { type });
      expect(isValidImageType(file)).toBe(expected);
    });
  });

  describe("isValidImageSize", () => {
    it("should return true for file size equal to max", () => {
      const file = new File([new ArrayBuffer(MAX_IMAGE_SIZE)], "test.jpg", {
        type: "image/jpeg",
      });
      expect(isValidImageSize(file)).toBe(true);
    });

    it("should return true for file size less than max", () => {
      const file = new File([new ArrayBuffer(MAX_IMAGE_SIZE - 1)], "test.jpg", {
        type: "image/jpeg",
      });
      expect(isValidImageSize(file)).toBe(true);
    });

    it("should return false for file size greater than max", () => {
      const file = new File([new ArrayBuffer(MAX_IMAGE_SIZE + 1)], "test.jpg", {
        type: "image/jpeg",
      });
      expect(isValidImageSize(file)).toBe(false);
    });

    it("should return true for zero size file", () => {
      const file = new File([], "test.jpg", { type: "image/jpeg" });
      expect(isValidImageSize(file)).toBe(true);
    });
  });

  describe("validateImageFile", () => {
    it("should return valid for valid image type and size", () => {
      const file = new File([new ArrayBuffer(1000)], "test.jpg", {
        type: "image/jpeg",
      });
      const result = validateImageFile(file);
      expect(result).toEqual({ valid: true });
    });

    it("should return invalid for invalid image type", () => {
      const file = new File([new ArrayBuffer(1000)], "test.pdf", {
        type: "application/pdf",
      });
      const result = validateImageFile(file);
      expect(result).toEqual({
        valid: false,
        error: "Invalid file type. Please select an image file.",
      });
    });

    it("should return invalid for file size exceeding max", () => {
      const file = new File([new ArrayBuffer(MAX_IMAGE_SIZE + 1)], "test.jpg", {
        type: "image/jpeg",
      });
      const result = validateImageFile(file);
      expect(result).toEqual({
        valid: false,
        error: "File size must be less than 5MB",
      });
    });

    it("should return invalid for invalid type even if size is valid", () => {
      const file = new File([new ArrayBuffer(1000)], "test.txt", {
        type: "text/plain",
      });
      const result = validateImageFile(file);
      expect(result).toEqual({
        valid: false,
        error: "Invalid file type. Please select an image file.",
      });
    });
  });
});
