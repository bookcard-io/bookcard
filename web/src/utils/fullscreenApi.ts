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

/**
 * Fullscreen API utilities.
 *
 * Provides centralized functions for interacting with the browser's Fullscreen API.
 * Follows DRY by centralizing fullscreen API operations.
 * Follows SRP by focusing solely on fullscreen API interactions.
 */

/**
 * Checks if the Fullscreen API is supported in the current browser.
 *
 * Returns
 * -------
 * boolean
 *     True if the Fullscreen API is supported.
 */
export function isFullscreenSupported(): boolean {
  return !!(
    document.documentElement.requestFullscreen ||
    (
      document.documentElement as unknown as {
        webkitRequestFullscreen?: () => Promise<void>;
      }
    ).webkitRequestFullscreen ||
    (
      document.documentElement as unknown as {
        mozRequestFullScreen?: () => Promise<void>;
      }
    ).mozRequestFullScreen ||
    (
      document.documentElement as unknown as {
        msRequestFullscreen?: () => Promise<void>;
      }
    ).msRequestFullscreen
  );
}

/**
 * Gets the current fullscreen element.
 *
 * Handles browser-specific fullscreen element properties.
 *
 * Returns
 * -------
 * Element | null
 *     The element currently in fullscreen, or null if none.
 */
export function getFullscreenElement(): Element | null {
  return (
    document.fullscreenElement ||
    (document as unknown as { webkitFullscreenElement?: Element | null })
      .webkitFullscreenElement ||
    (document as unknown as { mozFullScreenElement?: Element | null })
      .mozFullScreenElement ||
    (document as unknown as { msFullscreenElement?: Element | null })
      .msFullscreenElement ||
    null
  );
}

/**
 * Checks if any element is currently in fullscreen mode.
 *
 * Returns
 * -------
 * boolean
 *     True if an element is in fullscreen mode.
 */
export function isFullscreen(): boolean {
  return getFullscreenElement() !== null;
}

/**
 * Requests fullscreen for the document element.
 *
 * Handles browser-specific fullscreen request methods.
 *
 * Returns
 * -------
 * Promise<void>
 *     Promise that resolves when fullscreen is entered.
 */
export async function requestFullscreen(): Promise<void> {
  const element = document.documentElement;

  if (element.requestFullscreen) {
    await element.requestFullscreen();
  } else if (
    (element as unknown as { webkitRequestFullscreen?: () => Promise<void> })
      .webkitRequestFullscreen
  ) {
    await (
      element as unknown as { webkitRequestFullscreen: () => Promise<void> }
    ).webkitRequestFullscreen();
  } else if (
    (element as unknown as { mozRequestFullScreen?: () => Promise<void> })
      .mozRequestFullScreen
  ) {
    await (
      element as unknown as { mozRequestFullScreen: () => Promise<void> }
    ).mozRequestFullScreen();
  } else if (
    (element as unknown as { msRequestFullscreen?: () => Promise<void> })
      .msRequestFullscreen
  ) {
    await (
      element as unknown as { msRequestFullscreen: () => Promise<void> }
    ).msRequestFullscreen();
  } else {
    throw new Error("Fullscreen API is not supported");
  }
}

/**
 * Exits fullscreen mode.
 *
 * Handles browser-specific fullscreen exit methods.
 *
 * Returns
 * -------
 * Promise<void>
 *     Promise that resolves when fullscreen is exited.
 */
export async function exitFullscreen(): Promise<void> {
  if (document.exitFullscreen) {
    await document.exitFullscreen();
  } else if (
    (document as unknown as { webkitExitFullscreen?: () => Promise<void> })
      .webkitExitFullscreen
  ) {
    await (
      document as unknown as { webkitExitFullscreen: () => Promise<void> }
    ).webkitExitFullscreen();
  } else if (
    (document as unknown as { mozCancelFullScreen?: () => Promise<void> })
      .mozCancelFullScreen
  ) {
    await (
      document as unknown as { mozCancelFullScreen: () => Promise<void> }
    ).mozCancelFullScreen();
  } else if (
    (document as unknown as { msExitFullscreen?: () => Promise<void> })
      .msExitFullscreen
  ) {
    await (
      document as unknown as { msExitFullscreen: () => Promise<void> }
    ).msExitFullscreen();
  } else {
    throw new Error("Fullscreen API is not supported");
  }
}

/**
 * Gets the fullscreen change event name for the current browser.
 *
 * Returns
 * -------
 * string
 *     The event name to listen for fullscreen changes.
 */
export function getFullscreenChangeEventName(): string {
  if (document.fullscreenElement !== undefined) {
    return "fullscreenchange";
  }
  if (
    (document as unknown as { webkitFullscreenElement?: unknown })
      .webkitFullscreenElement !== undefined
  ) {
    return "webkitfullscreenchange";
  }
  if (
    (document as unknown as { mozFullScreenElement?: unknown })
      .mozFullScreenElement !== undefined
  ) {
    return "mozfullscreenchange";
  }
  if (
    (document as unknown as { msFullscreenElement?: unknown })
      .msFullscreenElement !== undefined
  ) {
    return "MSFullscreenChange";
  }
  return "fullscreenchange";
}
