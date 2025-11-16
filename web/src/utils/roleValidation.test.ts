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
import {
  validateRoleDescription,
  validateRoleForm,
  validateRoleName,
} from "./roleValidation";

describe("roleValidation utils", () => {
  describe("validateRoleName", () => {
    it("should return undefined for valid name", () => {
      expect(validateRoleName("valid-name")).toBeUndefined();
      expect(validateRoleName("a")).toBeUndefined();
      expect(validateRoleName("a".repeat(64))).toBeUndefined();
    });

    it("should return error for empty name", () => {
      expect(validateRoleName("")).toBe("Name is required");
      expect(validateRoleName("   ")).toBe("Name is required");
    });

    it("should return error for name that is too short after trim", () => {
      expect(validateRoleName(" ")).toBe("Name is required");
    });

    it("should return error for name that is too long", () => {
      expect(validateRoleName("a".repeat(65))).toBe(
        "Name must be at most 64 characters",
      );
    });

    it("should trim whitespace before validation", () => {
      expect(validateRoleName("  valid-name  ")).toBeUndefined();
      expect(validateRoleName("  ")).toBe("Name is required");
    });
  });

  describe("validateRoleDescription", () => {
    it("should return undefined for valid description", () => {
      expect(validateRoleDescription("")).toBeUndefined();
      expect(validateRoleDescription("Valid description")).toBeUndefined();
      expect(validateRoleDescription("a".repeat(255))).toBeUndefined();
    });

    it("should return error for description that is too long", () => {
      expect(validateRoleDescription("a".repeat(256))).toBe(
        "Description must be at most 255 characters",
      );
    });
  });

  describe("validateRoleForm", () => {
    it("should return empty errors object for valid form data", () => {
      const validData = {
        name: "valid-name",
        description: "Valid description",
      };
      const errors = validateRoleForm(validData);
      expect(errors).toEqual({});
    });

    it("should return errors for invalid name", () => {
      const invalidData = {
        name: "",
        description: "Valid description",
      };
      const errors = validateRoleForm(invalidData);
      expect(errors.name).toBe("Name is required");
      expect(errors.description).toBeUndefined();
    });

    it("should return errors for invalid description", () => {
      const invalidData = {
        name: "valid-name",
        description: "a".repeat(256),
      };
      const errors = validateRoleForm(invalidData);
      expect(errors.name).toBeUndefined();
      expect(errors.description).toBe(
        "Description must be at most 255 characters",
      );
    });

    it("should return multiple errors for multiple invalid fields", () => {
      const invalidData = {
        name: "",
        description: "a".repeat(256),
      };
      const errors = validateRoleForm(invalidData);
      expect(errors.name).toBe("Name is required");
      expect(errors.description).toBe(
        "Description must be at most 255 characters",
      );
    });

    it("should handle name at maximum length", () => {
      const validData = {
        name: "a".repeat(64),
        description: "Valid description",
      };
      const errors = validateRoleForm(validData);
      expect(errors).toEqual({});
    });

    it("should handle description at maximum length", () => {
      const validData = {
        name: "valid-name",
        description: "a".repeat(255),
      };
      const errors = validateRoleForm(validData);
      expect(errors).toEqual({});
    });

    it("should handle empty description as valid", () => {
      const validData = {
        name: "valid-name",
        description: "",
      };
      const errors = validateRoleForm(validData);
      expect(errors).toEqual({});
    });
  });
});
