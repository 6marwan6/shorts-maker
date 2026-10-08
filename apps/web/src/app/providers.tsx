"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

/**
 * impl plan §1.2: "TanStack Query for server-state fetching/caching". One QueryClient per
 * browser session (React state, not a module singleton) so it isn't shared across users
 * during SSR. No business logic lives here -- this is wiring only.
 */
export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
