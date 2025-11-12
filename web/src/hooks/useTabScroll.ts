import { useCallback, useRef } from "react";
import {
  calculateContainerScrollPosition,
  calculateScrollPosition,
  findScrollableParent,
  scrollContainerTo,
  scrollWindowTo,
} from "@/utils/scroll";

export interface UseTabScrollOptions {
  /** Delay in milliseconds before scrolling (default: 50). */
  scrollDelay?: number;
  /** Padding from top of viewport for header (default: 20). */
  paddingTop?: number;
  /** Padding from bottom of viewport for target (default: 20). */
  paddingBottom?: number;
  /** Scroll behavior (default: "smooth"). */
  behavior?: ScrollBehavior;
  /** Data attribute selector for tab content (default: 'data-tab-content'). */
  contentSelector?: string;
}

/**
 * Custom hook for scrolling to bottom-most element in tab content.
 *
 * Scrolls to show the last child element in the active tab's content while
 * ensuring a header element remains visible. Follows SRP by handling only
 * scroll behavior logic. Follows IOC by accepting configurable options.
 *
 * Parameters
 * ----------
 * options : UseTabScrollOptions
 *     Configuration options for scroll behavior.
 *
 * Returns
 * -------
 * object
 *     Object containing refs and scroll function:
 *     - headerRef: Ref for the header element
 *     - contentRef: Ref for the content container
 *     - scrollToBottom: Function to trigger scroll to bottom-most element
 */
export function useTabScroll<
  THeader extends HTMLElement = HTMLHeadingElement,
  TContent extends HTMLElement = HTMLDivElement,
>(options: UseTabScrollOptions = {}) {
  const {
    scrollDelay = 50,
    paddingTop = 20,
    paddingBottom = 20,
    behavior = "smooth",
    contentSelector = '[data-tab-content="true"]',
  } = options;

  const headerRef = useRef<THeader>(null);
  const contentRef = useRef<TContent>(null);

  /**
   * Scrolls to the bottom-most setting while keeping the header visible.
   *
   * Finds the last child element in the active tab's content and scrolls
   * to display it while ensuring the header remains visible in the viewport.
   */
  const scrollToBottom = useCallback(() => {
    if (!contentRef.current || !headerRef.current) {
      return;
    }

    // Wait for content to render after tab change
    setTimeout(() => {
      const contentContainer = contentRef.current;
      const headerElement = headerRef.current;

      if (!contentContainer || !headerElement) {
        return;
      }

      // Find the active tab's content div
      const activeContent = contentContainer.querySelector(
        contentSelector,
      ) as HTMLElement;

      if (!activeContent) {
        return;
      }

      // Get the last child element (bottom-most setting)
      const children = Array.from(activeContent.children);
      const lastChild = children[children.length - 1] as HTMLElement;

      if (!lastChild) {
        return;
      }

      // Get positions relative to viewport
      const headerRect = headerElement.getBoundingClientRect();
      const lastChildRect = lastChild.getBoundingClientRect();
      const viewportHeight = window.innerHeight;

      // Find the scrollable ancestor
      const scrollableParent = findScrollableParent(contentContainer);

      if (!scrollableParent) {
        // Scroll window
        const targetScrollY = calculateScrollPosition(
          headerRect,
          lastChildRect,
          viewportHeight,
          paddingTop,
          paddingBottom,
        );

        if (targetScrollY !== null) {
          scrollWindowTo(targetScrollY, behavior);
        }
      } else {
        // Scroll within container
        const targetScrollTop = calculateContainerScrollPosition(
          scrollableParent,
          headerRect,
          lastChildRect,
          paddingTop,
          paddingBottom,
        );

        if (targetScrollTop !== null) {
          scrollContainerTo(scrollableParent, targetScrollTop, behavior);
        }
      }
    }, scrollDelay);
  }, [scrollDelay, paddingTop, paddingBottom, behavior, contentSelector]);

  return {
    headerRef,
    contentRef,
    scrollToBottom,
  };
}
