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

"""Health check endpoints for the application.

Provides endpoints for Docker and load balancers to check application health.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def register_health_endpoints(app: FastAPI) -> None:
    """Register health check endpoints with the FastAPI application.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """

    @app.get("/health")
    async def health_check() -> JSONResponse:
        """Health check endpoint for Docker and load balancers.

        Returns
        -------
        JSONResponse
            JSON response with status "ok".
        """
        return JSONResponse(content={"status": "ok"})
