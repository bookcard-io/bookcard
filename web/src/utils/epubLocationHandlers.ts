import type { Book, Rendition } from "epubjs";
import {
  areLocationsReady,
  calculateProgressFromCfi,
  getCfiFromProgress,
} from "@/utils/epubLocation";

/**
 * Lightweight ref-like type used to avoid a hard dependency on React ref types.
 *
 * Parameters
 * ----------
 * T
 *     Referenced value type.
 */
export interface RefLike<T> {
  current: T;
}

/**
 * Options for ``createLocationChangedHandler``.
 *
 * Encapsulates all dependencies required to update location and progress
 * when the reader location changes.
 */
export interface LocationChangedHandlerOptions {
  /** Flag ref indicating whether navigation is currently in progress. */
  isNavigatingRef: RefLike<boolean>;
  /** Current location value from component state. */
  location: string | number;
  /** State updater for location. */
  setLocation: (loc: string | number) => void;
  /** Ref to the EPUB book instance. */
  bookRef: RefLike<Book | null>;
  /** Optional callback invoked when location and progress change. */
  onLocationChange?: (
    cfi: string,
    progress: number,
    skipBackendUpdate?: boolean,
  ) => void;
  /** Ref indicating whether the initial load phase is still active. */
  isInitialLoadRef: RefLike<boolean>;
  /** Ref holding the current debounce timeout identifier. */
  progressCalculationTimeoutRef: RefLike<ReturnType<typeof setTimeout> | null>;
}

/**
 * Factory for the ``locationChanged`` handler, responsible for updating
 * reader location and debounced progress calculation.
 *
 * Parameters
 * ----------
 * options : LocationChangedHandlerOptions
 *     Container for all dependencies required by the handler.
 *
 * Returns
 * -------
 * (loc: string) => void
 *     Handler passed to ``ReactReader`` ``locationChanged`` prop.
 */
export function createLocationChangedHandler(
  options: LocationChangedHandlerOptions,
): (loc: string) => void {
  const {
    isNavigatingRef,
    location,
    setLocation,
    bookRef,
    onLocationChange,
    isInitialLoadRef,
    progressCalculationTimeoutRef,
  } = options;

  return (loc: string) => {
    // Don't process if we're programmatically navigating
    if (isNavigatingRef.current) {
      return;
    }

    // Update location state only if it's different (avoid unnecessary updates)
    if (loc !== location) {
      setLocation(loc);
    }

    if (!bookRef.current || !onLocationChange) {
      return;
    }

    // During initial load, skip backend updates to prevent PUT requests
    const skipBackendUpdate = isInitialLoadRef.current;

    // Debounce progress calculation to avoid blocking page turns
    if (progressCalculationTimeoutRef.current) {
      clearTimeout(progressCalculationTimeoutRef.current);
    }

    progressCalculationTimeoutRef.current = setTimeout(() => {
      // Calculate progress using book.locations
      const book = bookRef.current;
      if (!book || !book.locations) {
        // During initial load, skip backend update
        if (skipBackendUpdate) {
          onLocationChange(loc, 0, true);
        } else {
          onLocationChange(loc, 0);
        }
        return;
      }

      // Check if locations are already generated/cached
      const locationsReady = areLocationsReady(book.locations);

      const calculateAndUpdateProgress = () => {
        const progress = calculateProgressFromCfi(book, loc);
        // During initial load, skip backend update
        if (skipBackendUpdate) {
          onLocationChange(loc, progress, true);
        } else {
          onLocationChange(loc, progress);
        }
      };

      if (locationsReady) {
        // Locations are already generated, calculate immediately
        calculateAndUpdateProgress();
      } else {
        // Generate locations asynchronously without blocking
        book.locations.generate(200).then(() => {
          calculateAndUpdateProgress();
        });
      }
    }, 100); // Small delay to avoid blocking page turns
  };
}

/**
 * Options for ``createJumpToProgressHandler``.
 *
 * Encapsulates all dependencies required to map a progress value to a CFI
 * and update both rendition and backend.
 */
export interface JumpToProgressHandlerOptions {
  /** Ref to the EPUB book instance. */
  bookRef: RefLike<Book | null>;
  /** Ref to the active rendition instance. */
  renditionRef: RefLike<Rendition | undefined>;
  /** Flag ref indicating whether navigation is currently in progress. */
  isNavigatingRef: RefLike<boolean>;
  /** State updater for location. */
  setLocation: (loc: string | number) => void;
  /** Optional callback invoked when location and progress change. */
  onLocationChange?: (
    cfi: string,
    progress: number,
    skipBackendUpdate?: boolean,
  ) => void;
}

/**
 * Factory for the ``jumpToProgress`` handler, responsible for mapping
 * progress values to CFIs and updating the rendition and backend.
 *
 * Parameters
 * ----------
 * options : JumpToProgressHandlerOptions
 *     Container for all dependencies required by the handler.
 *
 * Returns
 * -------
 * (progress: number) => void
 *     Handler registered via ``onJumpToProgress``.
 */
export function createJumpToProgressHandler(
  options: JumpToProgressHandlerOptions,
): (progress: number) => void {
  const {
    bookRef,
    renditionRef,
    isNavigatingRef,
    setLocation,
    onLocationChange,
  } = options;

  return (progress: number) => {
    const book = bookRef.current;
    const rendition = renditionRef.current;

    if (!book || !rendition) {
      return;
    }

    // Mark that we're programmatically navigating to prevent location callback from interfering
    isNavigatingRef.current = true;

    if (!book.locations) {
      isNavigatingRef.current = false;
      // eslint-disable-next-line no-console
      console.warn("Cannot jump to progress: locations not available");
      return;
    }

    // Check if locations are already generated/cached
    const locationsReady = areLocationsReady(book.locations);

    const performJump = () => {
      try {
        const cfi = getCfiFromProgress(book, progress);
        if (!cfi) {
          // eslint-disable-next-line no-console
          console.warn("Cannot jump to progress: could not get CFI");
          isNavigatingRef.current = false;
          return;
        }

        rendition.display(cfi);
        // Update location state to match
        setLocation(cfi);

        // Trigger location change callback with CFI and progress
        if (onLocationChange) {
          const actualProgress = calculateProgressFromCfi(book, cfi);
          onLocationChange(
            cfi,
            actualProgress,
            false, // Don't skip backend update - this is a user action
          );
        }
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error("Error jumping to progress:", error);
      } finally {
        // Reset flag after navigation completes
        setTimeout(() => {
          isNavigatingRef.current = false;
        }, 200);
      }
    };

    if (locationsReady) {
      // Locations are already generated, jump immediately
      performJump();
    } else {
      // Wait for locations to be generated and cached
      book.locations.generate(200).then(() => {
        performJump();
      });
    }
  };
}
