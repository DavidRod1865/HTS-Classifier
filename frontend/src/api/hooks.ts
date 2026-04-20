/**
 * TanStack Query hooks — the bridge between UI components and the API.
 *
 * Why hooks instead of calling the API directly?
 * TanStack Query (React Query) handles:
 *   - Loading states (isLoading, isPending)
 *   - Error states (isError, error)
 *   - Automatic retry on failure
 *   - Caching (don't re-fetch if we already have fresh data)
 *   - Deduplication (multiple components requesting the same data = 1 API call)
 *
 * This replaces ~180 lines of manual useState + fetch + error handling from v1.
 *
 * Usage in a component:
 *   const { mutate, data, isPending, error } = useClassify();
 *   mutate({ query: "cotton t-shirts" });
 */

import { useMutation } from "@tanstack/react-query";
import { classifyProduct, type ClassifyRequest, type ClassifyResponse } from "./client";

/**
 * Hook for classifying a product.
 *
 * Uses useMutation (not useQuery) because classification is a write-like
 * operation — it's triggered by user action (clicking "Search"), not by
 * the component mounting. useQuery is for "fetch data on render".
 *
 * Returns:
 *   mutate(request)  — call this to trigger classification
 *   data             — the ClassifyResponse (after success)
 *   isPending        — true while the request is in flight
 *   error            — Error object if the request failed
 *   reset()          — clear the result (for "new search")
 */
export function useClassify() {
  return useMutation<ClassifyResponse, Error, ClassifyRequest>({
    mutationFn: classifyProduct,
  });
}