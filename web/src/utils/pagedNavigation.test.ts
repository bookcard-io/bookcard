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
  detectSwipeAction,
  detectWheelEdgeNavigationAction,
  getPagedNavigationStrategy,
} from "./pagedNavigation";

describe("pagedNavigation strategies", () => {
  it("maps keys for ltr", () => {
    const s = getPagedNavigationStrategy("ltr");
    expect(s.mapKeyToAction("ArrowRight")).toBe("next");
    expect(s.mapKeyToAction("ArrowLeft")).toBe("previous");
    expect(s.mapKeyToAction("Home")).toBe("first");
    expect(s.mapKeyToAction("End")).toBe("last");
    expect(s.mapKeyToAction("UnrelatedKey")).toBeNull();
  });

  it("maps keys for rtl", () => {
    const s = getPagedNavigationStrategy("rtl");
    expect(s.mapKeyToAction("ArrowRight")).toBe("previous");
    expect(s.mapKeyToAction("ArrowLeft")).toBe("next");
  });

  it("maps keys for vertical", () => {
    const s = getPagedNavigationStrategy("vertical");
    expect(s.mapKeyToAction("ArrowDown")).toBe("next");
    expect(s.mapKeyToAction("ArrowUp")).toBe("previous");
    // Fallback keys remain available.
    expect(s.mapKeyToAction("ArrowRight")).toBe("next");
    expect(s.mapKeyToAction("ArrowLeft")).toBe("previous");
  });

  it("maps swipes for ltr/rtl/vertical", () => {
    const thresholdPx = 10;

    const ltr = getPagedNavigationStrategy("ltr");
    expect(ltr.mapSwipeToAction(50, 0, thresholdPx)).toBe("previous");
    expect(ltr.mapSwipeToAction(-50, 0, thresholdPx)).toBe("next");
    expect(ltr.mapSwipeToAction(5, 0, thresholdPx)).toBeNull();
    expect(ltr.mapSwipeToAction(50, 60, thresholdPx)).toBeNull();

    const rtl = getPagedNavigationStrategy("rtl");
    expect(rtl.mapSwipeToAction(50, 0, thresholdPx)).toBe("next");
    expect(rtl.mapSwipeToAction(-50, 0, thresholdPx)).toBe("previous");

    const vertical = getPagedNavigationStrategy("vertical");
    expect(vertical.mapSwipeToAction(0, -50, thresholdPx)).toBe("next");
    expect(vertical.mapSwipeToAction(0, 50, thresholdPx)).toBe("previous");
    expect(vertical.mapSwipeToAction(60, 50, thresholdPx)).toBeNull();
  });

  it("maps wheel for ltr/rtl/vertical", () => {
    const thresholdPx = 10;

    const ltr = getPagedNavigationStrategy("ltr");
    expect(ltr.mapWheelToAction(50, 0, thresholdPx)).toBe("next");
    expect(ltr.mapWheelToAction(-50, 0, thresholdPx)).toBe("previous");
    expect(ltr.mapWheelToAction(5, 0, thresholdPx)).toBeNull();
    expect(ltr.mapWheelToAction(10, 50, thresholdPx)).toBeNull();

    const rtl = getPagedNavigationStrategy("rtl");
    expect(rtl.mapWheelToAction(50, 0, thresholdPx)).toBe("previous");
    expect(rtl.mapWheelToAction(-50, 0, thresholdPx)).toBe("next");

    const vertical = getPagedNavigationStrategy("vertical");
    expect(vertical.mapWheelToAction(0, 50, thresholdPx)).toBe("next");
    expect(vertical.mapWheelToAction(0, -50, thresholdPx)).toBe("previous");
    expect(vertical.mapWheelToAction(50, 10, thresholdPx)).toBeNull();
  });
});

describe("detectSwipeAction", () => {
  it("returns null when gesture exceeds max duration", () => {
    const strategy = getPagedNavigationStrategy("ltr");

    const action = detectSwipeAction({
      startX: 0,
      startY: 0,
      endX: 200,
      endY: 0,
      durationMs: 999,
      maxDurationMs: 100,
      thresholdPx: 10,
      strategy,
    });

    expect(action).toBeNull();
  });

  it("returns next/previous based on strategy", () => {
    const strategy = getPagedNavigationStrategy("vertical");

    const nextAction = detectSwipeAction({
      startX: 0,
      startY: 0,
      endX: 0,
      endY: -200,
      durationMs: 50,
      maxDurationMs: 100,
      thresholdPx: 10,
      strategy,
    });
    expect(nextAction).toBe("next");

    const prevAction = detectSwipeAction({
      startX: 0,
      startY: 0,
      endX: 0,
      endY: 200,
      durationMs: 50,
      maxDurationMs: 100,
      thresholdPx: 10,
      strategy,
    });
    expect(prevAction).toBe("previous");
  });
});

describe("detectWheelEdgeNavigationAction", () => {
  it("is edge-gated for vertical direction", () => {
    const strategy = getPagedNavigationStrategy("vertical");

    const thresholdPx = 10;
    const edgeTolerancePx = 0;

    // Not at top edge -> previous should not trigger.
    expect(
      detectWheelEdgeNavigationAction({
        deltaX: 0,
        deltaY: -50,
        thresholdPx,
        edgeTolerancePx,
        strategy,
        scrollLeft: 0,
        scrollTop: 10,
        scrollWidth: 1000,
        scrollHeight: 2000,
        clientWidth: 1000,
        clientHeight: 1000,
      }),
    ).toBeNull();

    // At top edge -> previous triggers.
    expect(
      detectWheelEdgeNavigationAction({
        deltaX: 0,
        deltaY: -50,
        thresholdPx,
        edgeTolerancePx,
        strategy,
        scrollLeft: 0,
        scrollTop: 0,
        scrollWidth: 1000,
        scrollHeight: 2000,
        clientWidth: 1000,
        clientHeight: 1000,
      }),
    ).toBe("previous");

    // At bottom edge -> next triggers.
    expect(
      detectWheelEdgeNavigationAction({
        deltaX: 0,
        deltaY: 50,
        thresholdPx,
        edgeTolerancePx,
        strategy,
        scrollLeft: 0,
        scrollTop: 1000,
        scrollWidth: 1000,
        scrollHeight: 2000,
        clientWidth: 1000,
        clientHeight: 1000,
      }),
    ).toBe("next");
  });

  it("is edge-gated for ltr direction (horizontal axis)", () => {
    const strategy = getPagedNavigationStrategy("ltr");

    const thresholdPx = 10;
    const edgeTolerancePx = 0;

    // Not at start -> previous should not trigger (wheel left).
    expect(
      detectWheelEdgeNavigationAction({
        deltaX: -50,
        deltaY: 0,
        thresholdPx,
        edgeTolerancePx,
        strategy,
        scrollLeft: 10,
        scrollTop: 0,
        scrollWidth: 2000,
        scrollHeight: 1000,
        clientWidth: 1000,
        clientHeight: 1000,
      }),
    ).toBeNull();

    // At start -> previous triggers.
    expect(
      detectWheelEdgeNavigationAction({
        deltaX: -50,
        deltaY: 0,
        thresholdPx,
        edgeTolerancePx,
        strategy,
        scrollLeft: 0,
        scrollTop: 0,
        scrollWidth: 2000,
        scrollHeight: 1000,
        clientWidth: 1000,
        clientHeight: 1000,
      }),
    ).toBe("previous");

    // At end -> next triggers (wheel right).
    expect(
      detectWheelEdgeNavigationAction({
        deltaX: 50,
        deltaY: 0,
        thresholdPx,
        edgeTolerancePx,
        strategy,
        scrollLeft: 1000,
        scrollTop: 0,
        scrollWidth: 2000,
        scrollHeight: 1000,
        clientWidth: 1000,
        clientHeight: 1000,
      }),
    ).toBe("next");
  });
});
