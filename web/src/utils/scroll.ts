/**
 * Utility functions for scroll calculations and operations.
 *
 * Provides reusable scroll-related functions following DRY principle.
 * Follows SRP by focusing solely on scroll calculation logic.
 */

/**
 * Finds the nearest scrollable ancestor element.
 *
 * Traverses up the DOM tree to find the first element with scrollable overflow.
 * Follows SRP by handling only scrollable parent detection.
 *
 * Parameters
 * ----------
 * element : Element
 *     Starting element to search from.
 *
 * Returns
 * -------
 * Element | null
 *     The first scrollable ancestor, or null if none found.
 */
export function findScrollableParent(element: Element): Element | null {
  let current: Element | null = element;

  while (current) {
    const style = window.getComputedStyle(current);
    if (
      style.overflow === "auto" ||
      style.overflow === "scroll" ||
      style.overflowY === "auto" ||
      style.overflowY === "scroll"
    ) {
      return current;
    }
    current = current.parentElement;
  }

  return null;
}

/**
 * Calculates scroll position to show target element while keeping header visible.
 *
 * Determines the optimal scroll position that displays the target element
 * at the bottom of the viewport while ensuring the header remains visible.
 * Follows SRP by handling only scroll position calculation.
 *
 * Parameters
 * ----------
 * headerRect : DOMRect
 *     Bounding rectangle of the header element.
 * targetRect : DOMRect
 *     Bounding rectangle of the target element to scroll to.
 * viewportHeight : number
 *     Height of the viewport.
 * paddingTop : number
 *     Padding from top of viewport for header (default: 20).
 * paddingBottom : number
 *     Padding from bottom of viewport for target (default: 20).
 *
 * Returns
 * -------
 * number | null
 *     Calculated scroll position, or null if no scroll needed.
 */
export function calculateScrollPosition(
  headerRect: DOMRect,
  targetRect: DOMRect,
  viewportHeight: number,
  paddingTop: number = 20,
  paddingBottom: number = 20,
): number | null {
  // If both elements are already visible, no scroll needed
  if (
    targetRect.bottom <= viewportHeight &&
    headerRect.top >= 0 &&
    headerRect.top < viewportHeight
  ) {
    return null;
  }

  const headerTop = headerRect.top + window.scrollY;
  const targetBottom = targetRect.bottom + window.scrollY;

  // Calculate scroll position: show target at bottom, but keep header visible
  const targetScrollY = Math.max(
    headerTop - paddingTop,
    targetBottom - viewportHeight + paddingBottom,
  );

  return targetScrollY;
}

/**
 * Calculates scroll position within a scrollable container.
 *
 * Determines the optimal scroll position for a scrollable parent element
 * that displays the target element while keeping the header visible.
 * Follows SRP by handling only container scroll calculation.
 *
 * Parameters
 * ----------
 * scrollableParent : Element
 *     The scrollable container element.
 * headerRect : DOMRect
 *     Bounding rectangle of the header element.
 * targetRect : DOMRect
 *     Bounding rectangle of the target element.
 * paddingTop : number
 *     Padding from top for header (default: 20).
 * paddingBottom : number
 *     Padding from bottom for target (default: 20).
 *
 * Returns
 * -------
 * number | null
 *     Calculated scroll position, or null if no scroll needed.
 */
export function calculateContainerScrollPosition(
  scrollableParent: Element,
  headerRect: DOMRect,
  targetRect: DOMRect,
  paddingTop: number = 20,
  paddingBottom: number = 20,
): number | null {
  const parentRect = scrollableParent.getBoundingClientRect();
  const parentScrollTop = scrollableParent.scrollTop;
  const parentHeight = parentRect.height;

  const headerTopRelative = headerRect.top - parentRect.top;
  const targetBottomRelative = targetRect.bottom - parentRect.top;

  const headerTopAbsolute = parentScrollTop + headerTopRelative;
  const targetBottomAbsolute = parentScrollTop + targetBottomRelative;

  const targetScrollTop = Math.max(
    headerTopAbsolute - paddingTop,
    targetBottomAbsolute - parentHeight + paddingBottom,
  );

  return targetScrollTop;
}

/**
 * Scrolls to position using window scroll.
 *
 * Parameters
 * ----------
 * scrollY : number
 *     Target scroll position.
 * behavior : ScrollBehavior
 *     Scroll behavior (default: "smooth").
 */
export function scrollWindowTo(
  scrollY: number,
  behavior: ScrollBehavior = "smooth",
): void {
  window.scrollTo({
    top: scrollY,
    behavior,
  });
}

/**
 * Scrolls to position within a scrollable container.
 *
 * Parameters
 * ----------
 * container : Element
 *     The scrollable container element.
 * scrollTop : number
 *     Target scroll position.
 * behavior : ScrollBehavior
 *     Scroll behavior (default: "smooth").
 */
export function scrollContainerTo(
  container: Element,
  scrollTop: number,
  behavior: ScrollBehavior = "smooth",
): void {
  container.scrollTo({
    top: scrollTop,
    behavior,
  });
}
