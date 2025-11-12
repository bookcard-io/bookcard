import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * PUT /api/auth/password
 *
 * Proxies password change request to the backend, then logs out the user
 * to invalidate the current token.
 */
export async function PUT(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const body = await request.json();

    // Call backend password change endpoint
    const response = await client.request("/auth/password", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const data = await response.json();
      return NextResponse.json(
        { detail: data.detail || "Failed to change password" },
        { status: response.status },
      );
    }

    // Password change successful - now logout to invalidate token
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
    const logoutHeaders: HeadersInit = {
      "Content-Type": "application/json",
    };
    if (token) {
      logoutHeaders.Authorization = `Bearer ${token}`;
    }

    // Call backend logout endpoint to blacklist the token
    await fetch(`${BACKEND_URL}/auth/logout`, {
      method: "POST",
      headers: logoutHeaders,
      credentials: "include",
    });

    // Clear authentication cookie
    const nextResponse = NextResponse.json(
      { detail: "Password changed successfully" },
      { status: 200 },
    );
    nextResponse.cookies.delete(AUTH_COOKIE_NAME);

    return nextResponse;
  } catch (error) {
    console.error("Error in PUT /api/auth/password:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
