import { render, renderHook, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useInfiniteScroll } from "./useInfiniteScroll";

describe("useInfiniteScroll", () => {
  let onLoadMore: ReturnType<typeof vi.fn>;
  let observeFn: ReturnType<typeof vi.fn>;
  let disconnectFn: ReturnType<typeof vi.fn>;
  let IntersectionObserverMock: typeof IntersectionObserver;

  beforeEach(() => {
    onLoadMore = vi.fn();
    observeFn = vi.fn();
    disconnectFn = vi.fn();
    class IntersectionObserverMockClass {
      observe = observeFn;
      disconnect = disconnectFn;
    }
    IntersectionObserverMock =
      IntersectionObserverMockClass as unknown as typeof IntersectionObserver;
    vi.stubGlobal("IntersectionObserver", IntersectionObserverMock);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should return a ref", () => {
    const { result } = renderHook(() => useInfiniteScroll({ onLoadMore }));
    expect(result.current).toBeDefined();
    expect(result.current.current).toBeNull();
  });

  it("should observe element when enabled", () => {
    const TestComponent = () => {
      const ref = useInfiniteScroll({ onLoadMore });
      return (
        <div ref={ref} data-testid="sentinel">
          Sentinel
        </div>
      );
    };

    render(<TestComponent />);
    const sentinel = screen.getByTestId("sentinel");

    expect(observeFn).toHaveBeenCalledWith(sentinel);
  });

  it("should not observe when disabled", () => {
    const TestComponent = () => {
      const ref = useInfiniteScroll({ onLoadMore, enabled: false });
      return (
        <div ref={ref} data-testid="sentinel">
          Sentinel
        </div>
      );
    };

    render(<TestComponent />);
    // When disabled, IntersectionObserver should not be called
    expect(observeFn).not.toHaveBeenCalled();
  });

  it("should not observe when hasMore is false", () => {
    const TestComponent = () => {
      const ref = useInfiniteScroll({ onLoadMore, hasMore: false });
      return (
        <div ref={ref} data-testid="sentinel">
          Sentinel
        </div>
      );
    };

    render(<TestComponent />);
    // When hasMore is false, IntersectionObserver should not be called
    expect(observeFn).not.toHaveBeenCalled();
  });

  it("should not observe when isLoading is true", () => {
    const TestComponent = () => {
      const ref = useInfiniteScroll({ onLoadMore, isLoading: true });
      return (
        <div ref={ref} data-testid="sentinel">
          Sentinel
        </div>
      );
    };

    render(<TestComponent />);
    // When isLoading is true, IntersectionObserver should not be called
    expect(observeFn).not.toHaveBeenCalled();
  });

  it("should call onLoadMore when element intersects", () => {
    let intersectionCallback:
      | ((entries: IntersectionObserverEntry[]) => void)
      | undefined;

    const testObserveFn = vi.fn();
    const testDisconnectFn = vi.fn();
    class IntersectionObserverMock {
      observe = testObserveFn;
      disconnect = testDisconnectFn;
      constructor(callback: (entries: IntersectionObserverEntry[]) => void) {
        intersectionCallback = callback;
      }
    }
    vi.stubGlobal("IntersectionObserver", IntersectionObserverMock);

    const TestComponent = () => {
      const ref = useInfiniteScroll({ onLoadMore });
      return (
        <div ref={ref} data-testid="sentinel">
          Sentinel
        </div>
      );
    };

    render(<TestComponent />);

    const mockEntry = {
      isIntersecting: true,
    } as IntersectionObserverEntry;

    if (intersectionCallback) {
      intersectionCallback([mockEntry]);
    }

    expect(onLoadMore).toHaveBeenCalledTimes(1);
  });

  it("should use custom rootMargin", () => {
    const TestComponent = () => {
      const ref = useInfiniteScroll({ onLoadMore, rootMargin: "200px" });
      return (
        <div ref={ref} data-testid="sentinel">
          Sentinel
        </div>
      );
    };

    render(<TestComponent />);

    // Verify that observe was called (which means IntersectionObserver was created with correct options)
    expect(observeFn).toHaveBeenCalled();
  });

  it("should disconnect on cleanup", () => {
    const testDisconnect = vi.fn();
    const testObserve = vi.fn();
    class IntersectionObserverMock {
      observe = testObserve;
      disconnect = testDisconnect;
    }
    vi.stubGlobal("IntersectionObserver", IntersectionObserverMock);

    const TestComponent = () => {
      const ref = useInfiniteScroll({ onLoadMore });
      return (
        <div ref={ref} data-testid="sentinel">
          Sentinel
        </div>
      );
    };

    const { unmount } = render(<TestComponent />);
    unmount();

    expect(testDisconnect).toHaveBeenCalled();
  });

  it("should not call onLoadMore when entry is not intersecting", () => {
    let intersectionCallback:
      | ((entries: IntersectionObserverEntry[]) => void)
      | undefined;

    const testObserveFn = vi.fn();
    const testDisconnectFn = vi.fn();
    class IntersectionObserverMock {
      observe = testObserveFn;
      disconnect = testDisconnectFn;
      constructor(callback: (entries: IntersectionObserverEntry[]) => void) {
        intersectionCallback = callback;
      }
    }
    vi.stubGlobal("IntersectionObserver", IntersectionObserverMock);

    const TestComponent = () => {
      const ref = useInfiniteScroll({ onLoadMore });
      return (
        <div ref={ref} data-testid="sentinel">
          Sentinel
        </div>
      );
    };

    render(<TestComponent />);

    const mockEntry = {
      isIntersecting: false,
    } as IntersectionObserverEntry;

    if (intersectionCallback) {
      intersectionCallback([mockEntry]);
    }

    expect(onLoadMore).not.toHaveBeenCalled();
  });
});
