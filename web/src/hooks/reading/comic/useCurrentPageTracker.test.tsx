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

import { render } from "@testing-library/react";
import { createRef } from "react";
import { describe, expect, it, vi } from "vitest";
import {
  type CurrentPageTracker,
  useCurrentPageTracker,
} from "./useCurrentPageTracker";

function Harness(props: {
  initialPage?: number;
  trackerRef: React.RefObject<CurrentPageTracker | null>;
}): null {
  const tracker = useCurrentPageTracker(props.initialPage);
  props.trackerRef.current = tracker;
  return null;
}

describe("useCurrentPageTracker", () => {
  it("initializes with default page 1", () => {
    const trackerRef = createRef<CurrentPageTracker>();
    render(<Harness trackerRef={trackerRef} />);
    const tracker = trackerRef.current;
    if (!tracker) throw new Error("Expected tracker to be set");
    expect(tracker.getCurrentPage()).toBe(1);
  });

  it("initializes with provided initial page", () => {
    const trackerRef = createRef<CurrentPageTracker>();
    render(<Harness initialPage={5} trackerRef={trackerRef} />);
    const tracker = trackerRef.current;
    if (!tracker) throw new Error("Expected tracker to be set");
    expect(tracker.getCurrentPage()).toBe(5);
  });

  it("updates current page", () => {
    const trackerRef = createRef<CurrentPageTracker>();
    render(<Harness initialPage={3} trackerRef={trackerRef} />);
    const tracker = trackerRef.current;
    if (!tracker) throw new Error("Expected tracker to be set");

    tracker.updateCurrentPage(7);
    expect(tracker.getCurrentPage()).toBe(7);

    tracker.updateCurrentPage(2);
    expect(tracker.getCurrentPage()).toBe(2);
  });

  it("creates page change handler that updates tracker and calls callback", () => {
    const onPageChange = vi.fn();
    const trackerRef = createRef<CurrentPageTracker>();
    render(<Harness initialPage={1} trackerRef={trackerRef} />);
    const tracker = trackerRef.current;
    if (!tracker) throw new Error("Expected tracker to be set");

    const handler = tracker.createPageChangeHandler(onPageChange);

    handler(5, 10, 0.5);
    expect(tracker.getCurrentPage()).toBe(5);
    expect(onPageChange).toHaveBeenCalledWith(5, 10, 0.5);
  });

  it("creates page change handler that works without callback", () => {
    const trackerRef = createRef<CurrentPageTracker>();
    render(<Harness initialPage={1} trackerRef={trackerRef} />);
    const tracker = trackerRef.current;
    if (!tracker) throw new Error("Expected tracker to be set");

    const handler = tracker.createPageChangeHandler();

    handler(8, 10, 0.8);
    expect(tracker.getCurrentPage()).toBe(8);
  });
});
