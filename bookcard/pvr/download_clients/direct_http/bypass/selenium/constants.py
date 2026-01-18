# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Constants for Selenium bypass operations."""

# Challenge detection indicators
CLOUDFLARE_INDICATORS = [
    "just a moment",
    "verify you are human",
    "verifying you are human",
    "cloudflare.com/products/turnstile",
]

DDOS_GUARD_INDICATORS = [
    "ddos-guard",
    "ddos guard",
    "checking your browser before accessing",
    "complete the manual check to continue",
    "could not verify your browser automatically",
]

# Protection cookie names
CF_COOKIE_NAMES = {"cf_clearance", "__cf_bm", "cf_chl_2", "cf_chl_prog"}
DDG_COOKIE_NAMES = {
    "__ddg1_",
    "__ddg2_",
    "__ddg5_",
    "__ddg8_",
    "__ddg9_",
    "__ddg10_",
    "__ddgid_",
    "__ddgmark_",
    "ddg_last_challenge",
}

# Domains requiring full session cookies (not just protection cookies)
FULL_COOKIE_DOMAINS = {
    "z-lib.fm",
    "z-lib.gs",
    "z-lib.id",
    "z-library.sk",
    "zlibrary-global.se",
}

# Common screen resolutions with weights
COMMON_RESOLUTIONS = [
    (1920, 1080, 0.35),
    (1366, 768, 0.18),
    (1536, 864, 0.10),
    (1440, 900, 0.08),
    (1280, 720, 0.07),
    (1600, 900, 0.06),
    (1280, 800, 0.05),
    (2560, 1440, 0.04),
    (1680, 1050, 0.04),
    (1920, 1200, 0.03),
]

# Driver reset errors
DRIVER_RESET_ERRORS = {
    "WebDriverException",
    "SessionNotCreatedException",
    "TimeoutException",
    "MaxRetryError",
}

# CDP click selectors
CDP_CLICK_SELECTORS = [
    "#turnstile-widget div",  # Cloudflare Turnstile
    "#cf-turnstile div",  # Alternative CF Turnstile
    "iframe[src*='challenges']",  # CF challenge iframe
    "input[type='checkbox']",  # Generic checkbox (DDOS-Guard)
    "[class*='checkbox']",  # Class-based checkbox
    "[class*='cb-i']",  # DDOS-Guard checkbox (seen in some templates)
    "#challenge-running",  # CF challenge indicator
]

CDP_GUI_CLICK_SELECTORS = [
    "#turnstile-widget div",  # Cloudflare Turnstile
    "#cf-turnstile div",  # Alternative CF Turnstile
    "#challenge-stage div",  # CF challenge stage
    "input[type='checkbox']",  # Generic checkbox
    "[class*='cb-i']",  # DDOS-Guard checkbox
]

# Bypass thresholds
#
# NOTE:
# Some providers (notably DDoS-Guard) can keep reporting the same challenge type
# while still requiring multiple different interaction strategies to succeed.
# If we abort too early, we never reach the later methods (GUI click / humanlike).
# Keep this high enough to allow a full method cycle.
MAX_CONSECUTIVE_SAME_CHALLENGE = 10
MIN_CONTENT_LENGTH_FOR_BYPASS = 100_000
MIN_EMOJI_COUNT = 3
MIN_BODY_LENGTH = 50

# Timing constants (in seconds)
HUMAN_DELAY_MIN = 0.5
HUMAN_DELAY_MAX = 1.5
CDP_DELAY_MIN = 1.0
CDP_DELAY_MAX = 2.0
CAPTCHA_WAIT_MIN = 3.0
CAPTCHA_WAIT_MAX = 5.0
RETRY_WAIT_BASE = 2.0
RETRY_WAIT_MAX = 12.0
NO_CHALLENGE_WAIT_MIN = 2.0
NO_CHALLENGE_WAIT_MAX = 3.0

# Display padding (for browser chrome)
DISPLAY_WIDTH_PADDING = 100
DISPLAY_HEIGHT_PADDING = 150

# Default retry counts
DEFAULT_MAX_BYPASS_RETRIES = 6
DEFAULT_MAX_FETCH_RETRIES = 3
