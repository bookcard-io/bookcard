"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type React from "react";
import { useState } from "react";
import { GlobalMessageHost } from "@/components/common/GlobalMessageHost";
import { ThemeInitializer } from "@/components/ThemeInitializer";
import { GlobalMessageProvider } from "@/contexts/GlobalMessageContext";

/**
 * Root providers component.
 *
 * Wraps the application with global client-side providers such as the
 * React Query client, global message provider, and theme initializer.
 *
 * Parameters
 * ----------
 * children : React.ReactNode
 *     The React node tree for the current page.
 *
 * Returns
 * -------
 * JSX.Element
 *     The wrapped component tree with all providers applied.
 */
export function RootProviders({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60, // 1 minute
            gcTime: 1000 * 60 * 5, // 5 minutes
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <GlobalMessageProvider>
        <ThemeInitializer>
          {children}
          <GlobalMessageHost />
        </ThemeInitializer>
      </GlobalMessageProvider>
    </QueryClientProvider>
  );
}
