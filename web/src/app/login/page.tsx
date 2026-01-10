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

"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { INSPIRING_QUOTES } from "@/constants/inspiring_quotes";
import { Eye } from "@/icons/Eye";
import { EyeSlash } from "@/icons/EyeSlash";

interface LoginFormData {
  identifier: string;
  password: string;
}

interface AuthConfig {
  oidc_enabled: boolean;
  oidc_issuer: string;
  local_login_enabled: boolean;
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [formData, setFormData] = useState<LoginFormData>({
    identifier: "",
    password: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [randomQuote, setRandomQuote] = useState<
    (typeof INSPIRING_QUOTES)[number] | null
  >(null);
  const referrer = searchParams.get("referrer");
  const showPasswordChangeSuccess = referrer === "password-change";

  // Select a random quote on client-side mount only
  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * INSPIRING_QUOTES.length);
    const quote = INSPIRING_QUOTES[randomIndex];
    if (quote) {
      setRandomQuote(quote);
    }
  }, []);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const resp = await fetch("/api/auth/config", { cache: "no-store" });
        const data = await resp.json();
        if (resp.ok) {
          setAuthConfig(data as AuthConfig);
        }
      } catch {
        // If config fetch fails, fall back to local login UI.
        setAuthConfig({
          oidc_enabled: false,
          oidc_issuer: "",
          local_login_enabled: true,
        });
      }
    };
    loadConfig();
  }, []);

  // Determine font size classes based on quote length
  const getQuoteFontSizeClasses = (quote: string) => {
    const length = quote.length;
    // Very long quotes (>400 chars) - smallest base, minimal scaling
    if (length > 400) {
      return "text-sm sm:text-base md:text-lg lg:text-xl";
    }
    // Long quotes (300-400 chars) - very small base, very conservative scaling
    if (length > 300) {
      return "text-sm sm:text-base md:text-lg lg:text-xl";
    }
    // Medium-long quotes (250-300 chars) - small base, conservative scaling
    if (length > 250) {
      return "text-base sm:text-lg md:text-xl lg:text-2xl";
    }
    // Medium-long quotes (200-250 chars) - moderate base, moderate scaling
    if (length > 200) {
      return "text-base sm:text-lg md:text-xl lg:text-2xl";
    }
    // Medium quotes (120-200 chars) - standard scaling
    if (length > 120) {
      return "text-lg sm:text-xl md:text-2xl lg:text-3xl";
    }
    // Short quotes (<120 chars) - larger, more prominent but still constrained
    return "text-xl sm:text-2xl md:text-3xl lg:text-4xl";
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (authConfig?.oidc_enabled && !authConfig.local_login_enabled) {
      setError("Local login is disabled. Please use SSO.");
      return;
    }
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        // Ensure the auth cookie set by the route handler is accepted/stored.
        credentials: "include",
        body: JSON.stringify({
          identifier: formData.identifier,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Invalid credentials");
        setIsLoading(false);
        return;
      }

      // Redirect to the next page or home
      const next = searchParams.get("next") || "/";
      router.push(next);
      router.refresh();
    } catch {
      setError("An error occurred. Please try again.");
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    // Clear error when user starts typing
    if (error) {
      setError(null);
    }
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-[var(--color-surface-a0)] p-8 before:pointer-events-none before:absolute before:top-0 before:right-0 before:z-0 before:h-full before:w-full before:bg-[radial-gradient(ellipse_80%_60%_at_top_right,rgba(144,170,249,0.18)_0%,rgba(144,170,249,0.10)_30%,transparent_70%)] before:content-[''] after:pointer-events-none after:absolute after:top-0 after:right-0 after:z-0 after:h-full after:w-full after:bg-[linear-gradient(135deg,transparent_0%,transparent_40%,rgba(144,170,249,0.06)_60%,transparent_100%)] after:content-['']">
      {/* Quote display - positioned between top of viewport and middle of form's top edge */}
      {randomQuote && (
        <div
          className="pointer-events-none absolute top-0 right-0 left-0 z-[1] flex items-center justify-center px-4 sm:px-8"
          style={{ bottom: "calc(50vh + 14rem)" }}
        >
          <div className="w-full max-w-4xl text-center">
            <blockquote
              className={`mb-2 max-h-[12rem] overflow-hidden font-medium text-[var(--color-text-a10)] leading-relaxed sm:mb-3 sm:max-h-[14rem] ${getQuoteFontSizeClasses(randomQuote.quote)}`}
            >
              "{randomQuote.quote}"
            </blockquote>
            <cite className="text-[var(--color-text-a30)] text-sm italic sm:text-base md:text-lg">
              — {randomQuote.author}
              {randomQuote.source && (
                <span className="text-[var(--color-text-a40)] not-italic">
                  {" "}
                  ({randomQuote.source})
                </span>
              )}
            </cite>
          </div>
        </div>
      )}

      <div className="relative z-[1] w-full max-w-[28rem] rounded-md bg-[var(--color-surface-tonal-a0)] p-10 shadow-[0_4px_6px_-1px_rgba(0,0,0,0.1),0_2px_4px_-1px_rgba(0,0,0,0.06)]">
        <div className="mb-8">
          <h1 className="mb-2 font-bold text-[1.875rem] text-[var(--color-text-a0)] leading-tight">
            Sign in to Bookcard
          </h1>
          <p className="text-[var(--color-text-a30)] text-sm leading-normal">
            Welcome back! Please enter your details.
          </p>
        </div>

        <div className="flex flex-col gap-6">
          {authConfig?.oidc_enabled && (
            <a
              href={`/api/auth/oidc/login?next=${encodeURIComponent(
                searchParams.get("next") || "/",
              )}`}
              className="inline-flex w-full items-center justify-center rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-a0)] px-4 py-3 font-medium text-[var(--color-text-a0)] text-base leading-normal transition-[border-color,box-shadow,background-color] duration-200 hover:bg-[var(--color-surface-a10)] focus:shadow-[0_0_0_3px_rgba(144,170,249,0.2)] focus:outline-none"
            >
              Sign in with SSO
            </a>
          )}

          {authConfig?.oidc_enabled && !authConfig.local_login_enabled && (
            <p className="text-[var(--color-text-a30)] text-sm leading-normal">
              Local login is disabled because SSO authentication is enabled.
            </p>
          )}

          {(!authConfig || authConfig.local_login_enabled) && (
            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
              {showPasswordChangeSuccess && (
                <output className="rounded-md border border-[var(--color-success-a0)] bg-[var(--color-success-a20)] px-4 py-3 text-[var(--color-success-a0)] text-sm leading-normal">
                  Password changed successfully! Please sign in again to
                  continue using the app.
                </output>
              )}
              {error && (
                <div
                  className="rounded-md border border-[var(--color-danger-a0)] bg-[rgba(156,33,33,0.2)] px-4 py-3 text-[var(--color-danger-a20)] text-sm leading-normal"
                  role="alert"
                >
                  {error}
                </div>
              )}

              <div className="flex flex-col gap-2">
                <label
                  htmlFor="identifier"
                  className="font-medium text-[var(--color-text-a10)] text-sm leading-normal"
                >
                  Username or Email
                </label>
                <input
                  id="identifier"
                  name="identifier"
                  type="text"
                  autoComplete="username"
                  className="w-full rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-a0)] px-4 py-3 text-[var(--color-text-a0)] text-base leading-normal transition-[border-color,box-shadow] duration-200 placeholder:text-[var(--color-text-a40)] focus:border-[var(--color-primary-a0)] focus:shadow-[0_0_0_3px_rgba(144,170,249,0.1)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                  placeholder="Enter your username or email"
                  value={formData.identifier}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="flex flex-col gap-2">
                <label
                  htmlFor="password"
                  className="font-medium text-[var(--color-text-a10)] text-sm leading-normal"
                >
                  Password
                </label>
                <div className="relative flex items-center">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    className="w-full rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-a0)] px-4 py-3 pr-12 text-[var(--color-text-a0)] text-base leading-normal transition-[border-color,box-shadow] duration-200 placeholder:text-[var(--color-text-a40)] focus:border-[var(--color-primary-a0)] focus:shadow-[0_0_0_3px_rgba(144,170,249,0.1)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 flex cursor-pointer items-center justify-center border-none bg-transparent p-1 text-[var(--color-text-a30)] transition-colors duration-200 hover:text-[var(--color-text-a10)] focus:text-[var(--color-primary-a0)] focus:outline-none"
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                  >
                    {showPassword ? (
                      <EyeSlash className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full cursor-pointer rounded-md border-none bg-[var(--color-primary-a0)] px-4 py-3 font-medium text-[var(--color-surface-a20)] text-base leading-normal transition-[background-color,opacity] duration-200 hover:bg-[var(--color-primary-a10)] focus:shadow-[0_0_0_3px_rgba(144,170,249,0.3)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 hover:disabled:bg-[var(--color-primary-a0)]"
              >
                {isLoading ? "Signing in..." : "Sign in"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-[var(--color-surface-a0)] p-8">
          <div className="relative z-[1] w-full max-w-[28rem] rounded-md bg-[var(--color-surface-tonal-a0)] p-10">
            <div className="mb-8">
              <h1 className="mb-2 font-bold text-[1.875rem] text-[var(--color-text-a0)] leading-tight">
                Sign in to Bookcard
              </h1>
              <p className="text-[var(--color-text-a30)] text-sm leading-normal">
                Loading...
              </p>
            </div>
          </div>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
