import { describe, expect, it } from "vitest";
import type { FlyoutPosition } from "@/hooks/useFlyoutPosition";
import { getFlyoutPositionStyle } from "./flyoutPositionStyle";

describe("flyoutPositionStyle utils", () => {
  describe("getFlyoutPositionStyle", () => {
    it("should return style with top position for right direction without left", () => {
      const position: FlyoutPosition = { top: 100 };
      const result = getFlyoutPositionStyle(position, "right");
      expect(result).toEqual({ top: "100px" });
    });

    it("should return style with top and left for right direction with left", () => {
      const position: FlyoutPosition = { top: 100, left: 200 };
      const result = getFlyoutPositionStyle(position, "right");
      expect(result).toEqual({ top: "100px", left: "200px" });
    });

    it("should return style with top position for left direction without right", () => {
      const position: FlyoutPosition = { top: 100 };
      const result = getFlyoutPositionStyle(position, "left");
      expect(result).toEqual({ top: "100px" });
    });

    it("should return style with top and right for left direction with right", () => {
      const position: FlyoutPosition = { top: 100, right: 200 };
      const result = getFlyoutPositionStyle(position, "left");
      expect(result).toEqual({ top: "100px", right: "200px" });
    });

    it("should not include left when direction is left even if left is defined", () => {
      const position: FlyoutPosition = { top: 100, left: 200 };
      const result = getFlyoutPositionStyle(position, "left");
      expect(result).toEqual({ top: "100px" });
    });

    it("should not include right when direction is right even if right is defined", () => {
      const position: FlyoutPosition = { top: 100, right: 200 };
      const result = getFlyoutPositionStyle(position, "right");
      expect(result).toEqual({ top: "100px" });
    });
  });
});
