import { type NextRequest, NextResponse } from "next/server";
import {
  AUTH_COOKIE_NAME,
  BACKEND_URL,
  COOKIE_SECURE,
} from "@/constants/config";

const POST_LOGIN_NEXT_COOKIE = "fundamental_post_login_next";

/**
 * GET /api/auth/oidc/callback
 *
 * Handles OIDC redirect, exchanges code via backend, and sets auth cookie.
 */
export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");
  if (!code || !state) {
    return NextResponse.json(
      { detail: "missing_code_or_state" },
      { status: 400 },
    );
  }

  const redirectUri = `${request.nextUrl.origin}/api/auth/oidc/callback`;
  const nextPath = request.cookies.get(POST_LOGIN_NEXT_COOKIE)?.value || "/";

  const response = await fetch(`${BACKEND_URL}/auth/oidc/callback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      code,
      state,
      redirect_uri: redirectUri,
    }),
  });

  const data = await response.json();
  if (!response.ok) {
    return NextResponse.json(
      { detail: data.detail || "oidc_callback_failed" },
      { status: response.status },
    );
  }

  const nextResponse = NextResponse.redirect(
    new URL(nextPath, request.nextUrl.origin),
  );

  // Clear the post-login cookie
  nextResponse.cookies.set(POST_LOGIN_NEXT_COOKIE, "", {
    httpOnly: true,
    secure: COOKIE_SECURE,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });

  // Set authentication cookie
  if (data.access_token) {
    nextResponse.cookies.set(AUTH_COOKIE_NAME, data.access_token, {
      httpOnly: true,
      secure: COOKIE_SECURE,
      sameSite: "lax",
      path: "/",
    });
  }

  return nextResponse;
}
