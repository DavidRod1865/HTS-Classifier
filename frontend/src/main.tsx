/**
 * Application entry point.
 *
 * Sets up two providers that wrap the entire app:
 *
 * 1. QueryClientProvider (TanStack Query)
 *    - Manages all API data fetching, caching, and retry logic
 *    - Without this, useQuery/useMutation hooks won't work
 *
 * 2. BrowserRouter (React Router)
 *    - Enables client-side routing (/search, /batch, /admin)
 *    - v1 used manual routing with window.location — v2 uses a proper router
 *      because we now have 3 distinct pages instead of 2
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";
import "./index.css";

// Create a QueryClient with sensible defaults.
// - retry: 1 means we retry failed requests once (not 3 times like the default)
// - staleTime: 30s means cached data is considered fresh for 30 seconds
//   (prevents re-fetching when switching tabs quickly)
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30 * 1000,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
);