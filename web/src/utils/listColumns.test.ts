import { describe, expect, it } from "vitest";
import { getColumnAlignClass, getColumnWidthStyles } from "./listColumns";

describe("listColumns utils", () => {
  describe("getColumnAlignClass", () => {
    it("should return left alignment classes", () => {
      expect(getColumnAlignClass("left")).toBe("justify-start text-left");
    });

    it("should return right alignment classes", () => {
      expect(getColumnAlignClass("right")).toBe("justify-end text-right");
    });

    it("should return center alignment classes for center", () => {
      expect(getColumnAlignClass("center")).toBe("justify-center text-center");
    });

    it("should return center alignment classes for undefined", () => {
      expect(getColumnAlignClass(undefined)).toBe("justify-center text-center");
    });
  });

  describe("getColumnWidthStyles", () => {
    it("should return empty object when minWidth is undefined", () => {
      expect(getColumnWidthStyles(undefined)).toEqual({});
    });

    it("should return empty object when minWidth is not provided", () => {
      expect(getColumnWidthStyles()).toEqual({});
    });

    it("should return width styles when minWidth is provided", () => {
      const minWidth = 200;
      const result = getColumnWidthStyles(minWidth);
      expect(result).toEqual({
        width: minWidth,
        minWidth: minWidth,
        maxWidth: minWidth,
        flexGrow: 0,
        flexShrink: 0,
        flexBasis: minWidth,
      });
    });

    it("should return empty object for zero minWidth", () => {
      const minWidth = 0;
      const result = getColumnWidthStyles(minWidth);
      expect(result).toEqual({}); // 0 is falsy, so returns empty object
    });
  });
});
