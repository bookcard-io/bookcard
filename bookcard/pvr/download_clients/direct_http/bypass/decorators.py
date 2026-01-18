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

"""Decorators for bypass operations."""

import logging
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def log_bypass_errors[**P, T](func: Callable[P, T | None]) -> Callable[P, T | None]:
    """Log errors from bypass operations.

    Works with both functions and methods. For methods, expects 'url' as the
    second parameter (after 'self').

    Parameters
    ----------
    func : Callable[P, T | None]
        Function or method to wrap.

    Returns
    -------
    Callable[P, T | None]
        Wrapped function with error logging.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
        """Log errors from bypass operations."""
        # Extract URL from args (first arg for functions, second for methods)
        url = args[0] if args else kwargs.get("url", "unknown")
        if len(args) > 1:
            url = args[1]  # For methods, url is the second parameter

        func_name = getattr(func, "__name__", "unknown")
        try:
            result = func(*args, **kwargs)
        except (
            TimeoutError,
            RuntimeError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as e:
            logger.warning("%s failed for '%s': %s", func_name, url, e)
            return None
        else:
            logger.debug("%s successful for '%s'", func_name, url)
            return result

    return wrapper
