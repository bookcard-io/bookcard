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
  validateConditionJson,
  validatePermissionAction,
  validatePermissionDescription,
  validatePermissionForm,
  validatePermissionName,
  validatePermissionResource,
} from "./permissionValidation";

describe("permissionValidation utils", () => {
  describe("validatePermissionName", () => {
    it("should return undefined for valid name", () => {
      expect(validatePermissionName("valid-name")).toBeUndefined();
      expect(validatePermissionName("a")).toBeUndefined();
      expect(validatePermissionName("a".repeat(100))).toBeUndefined();
    });

    it("should return error for empty name", () => {
      expect(validatePermissionName("")).toBe("Name is required");
      expect(validatePermissionName("   ")).toBe("Name is required");
    });

    it("should return error for name that is too short after trim", () => {
      expect(validatePermissionName(" ")).toBe("Name is required");
    });

    it("should return error for name that is too long", () => {
      expect(validatePermissionName("a".repeat(101))).toBe(
        "Name must be at most 100 characters",
      );
    });

    it("should trim whitespace before validation", () => {
      expect(validatePermissionName("  valid-name  ")).toBeUndefined();
      expect(validatePermissionName("  ")).toBe("Name is required");
    });
  });

  describe("validatePermissionDescription", () => {
    it("should return undefined for valid description", () => {
      expect(validatePermissionDescription("")).toBeUndefined();
      expect(
        validatePermissionDescription("Valid description"),
      ).toBeUndefined();
      expect(validatePermissionDescription("a".repeat(255))).toBeUndefined();
    });

    it("should return error for description that is too long", () => {
      expect(validatePermissionDescription("a".repeat(256))).toBe(
        "Description must be at most 255 characters",
      );
    });
  });

  describe("validatePermissionResource", () => {
    it("should return undefined for valid resource", () => {
      expect(validatePermissionResource("valid-resource")).toBeUndefined();
      expect(validatePermissionResource("a")).toBeUndefined();
      expect(validatePermissionResource("a".repeat(50))).toBeUndefined();
    });

    it("should return error for empty resource", () => {
      expect(validatePermissionResource("")).toBe("Resource is required");
      expect(validatePermissionResource("   ")).toBe("Resource is required");
    });

    it("should return error for resource that is too short after trim", () => {
      expect(validatePermissionResource(" ")).toBe("Resource is required");
    });

    it("should return error for resource that is too long", () => {
      expect(validatePermissionResource("a".repeat(51))).toBe(
        "Resource must be at most 50 characters",
      );
    });

    it("should trim whitespace before validation", () => {
      expect(validatePermissionResource("  valid-resource  ")).toBeUndefined();
      expect(validatePermissionResource("  ")).toBe("Resource is required");
    });
  });

  describe("validatePermissionAction", () => {
    it("should return undefined for valid action", () => {
      expect(validatePermissionAction("valid-action")).toBeUndefined();
      expect(validatePermissionAction("a")).toBeUndefined();
      expect(validatePermissionAction("a".repeat(50))).toBeUndefined();
    });

    it("should return error for empty action", () => {
      expect(validatePermissionAction("")).toBe("Action is required");
      expect(validatePermissionAction("   ")).toBe("Action is required");
    });

    it("should return error for action that is too short after trim", () => {
      expect(validatePermissionAction(" ")).toBe("Action is required");
    });

    it("should return error for action that is too long", () => {
      expect(validatePermissionAction("a".repeat(51))).toBe(
        "Action must be at most 50 characters",
      );
    });

    it("should trim whitespace before validation", () => {
      expect(validatePermissionAction("  valid-action  ")).toBeUndefined();
      expect(validatePermissionAction("  ")).toBe("Action is required");
    });
  });

  describe("validateConditionJson", () => {
    it("should return undefined for empty string", () => {
      expect(validateConditionJson("")).toBeUndefined();
      expect(validateConditionJson("   ")).toBeUndefined();
    });

    it("should return undefined for valid JSON", () => {
      expect(validateConditionJson("{}")).toBeUndefined();
      expect(validateConditionJson('{"key": "value"}')).toBeUndefined();
      expect(validateConditionJson('{"nested": {"key": 123}}')).toBeUndefined();
      expect(validateConditionJson("[]")).toBeUndefined();
      expect(validateConditionJson('["item1", "item2"]')).toBeUndefined();
    });

    it("should return error for invalid JSON", () => {
      const result = validateConditionJson("{invalid json}");
      expect(result).toBeDefined();
      expect(result).toContain("Invalid JSON");
    });

    it("should return error message with Error details when available", () => {
      const result = validateConditionJson("{invalid}");
      expect(result).toBeDefined();
      expect(result).toContain("Invalid JSON");
    });

    it("should handle non-Error exceptions", () => {
      // Mock JSON.parse to throw a non-Error
      const originalParse = JSON.parse;
      JSON.parse = () => {
        throw "string error";
      };

      const result = validateConditionJson("{test}");
      expect(result).toBe("Invalid JSON format");

      JSON.parse = originalParse;
    });
  });

  describe("validatePermissionForm", () => {
    it("should return empty errors object for valid form data", () => {
      const validData = {
        name: "valid-name",
        description: "Valid description",
        resource: "valid-resource",
        action: "valid-action",
        condition: "{}",
      };
      const errors = validatePermissionForm(validData);
      expect(errors).toEqual({});
    });

    it("should return errors for invalid name", () => {
      const invalidData = {
        name: "",
        description: "Valid description",
        resource: "valid-resource",
        action: "valid-action",
        condition: "{}",
      };
      const errors = validatePermissionForm(invalidData);
      expect(errors.name).toBe("Name is required");
      expect(errors.description).toBeUndefined();
      expect(errors.resource).toBeUndefined();
      expect(errors.action).toBeUndefined();
      expect(errors.condition).toBeUndefined();
    });

    it("should return errors for invalid description", () => {
      const invalidData = {
        name: "valid-name",
        description: "a".repeat(256),
        resource: "valid-resource",
        action: "valid-action",
        condition: "{}",
      };
      const errors = validatePermissionForm(invalidData);
      expect(errors.name).toBeUndefined();
      expect(errors.description).toBe(
        "Description must be at most 255 characters",
      );
    });

    it("should return errors for invalid resource", () => {
      const invalidData = {
        name: "valid-name",
        description: "Valid description",
        resource: "",
        action: "valid-action",
        condition: "{}",
      };
      const errors = validatePermissionForm(invalidData);
      expect(errors.name).toBeUndefined();
      expect(errors.description).toBeUndefined();
      expect(errors.resource).toBe("Resource is required");
    });

    it("should return errors for invalid action", () => {
      const invalidData = {
        name: "valid-name",
        description: "Valid description",
        resource: "valid-resource",
        action: "",
        condition: "{}",
      };
      const errors = validatePermissionForm(invalidData);
      expect(errors.name).toBeUndefined();
      expect(errors.description).toBeUndefined();
      expect(errors.resource).toBeUndefined();
      expect(errors.action).toBe("Action is required");
    });

    it("should return errors for invalid condition JSON", () => {
      const invalidData = {
        name: "valid-name",
        description: "Valid description",
        resource: "valid-resource",
        action: "valid-action",
        condition: "{invalid json}",
      };
      const errors = validatePermissionForm(invalidData);
      expect(errors.name).toBeUndefined();
      expect(errors.description).toBeUndefined();
      expect(errors.resource).toBeUndefined();
      expect(errors.action).toBeUndefined();
      expect(errors.condition).toBeDefined();
      expect(errors.condition).toContain("Invalid JSON");
    });

    it("should return multiple errors for multiple invalid fields", () => {
      const invalidData = {
        name: "",
        description: "a".repeat(256),
        resource: "",
        action: "",
        condition: "{invalid}",
      };
      const errors = validatePermissionForm(invalidData);
      expect(errors.name).toBe("Name is required");
      expect(errors.description).toBe(
        "Description must be at most 255 characters",
      );
      expect(errors.resource).toBe("Resource is required");
      expect(errors.action).toBe("Action is required");
      expect(errors.condition).toBeDefined();
    });

    it("should handle empty condition as valid", () => {
      const validData = {
        name: "valid-name",
        description: "Valid description",
        resource: "valid-resource",
        action: "valid-action",
        condition: "",
      };
      const errors = validatePermissionForm(validData);
      expect(errors).toEqual({});
    });
  });
});
