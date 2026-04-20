/**
 * API client — all backend communication goes through here.
 *
 * In v1, fetch() calls were scattered across App.jsx with duplicated
 * base URLs and error handling. In v2, everything is centralized here.
 *
 * The API_BASE_URL:
 *   - Development: empty string (Vite proxy handles /api → localhost:8080)
 *   - Production: set via VITE_API_URL env var (e.g., "https://api.htsoracle.com")
 */

// In dev, the Vite proxy forwards /api to the backend, so we use "".
// In prod, VITE_API_URL points to the deployed backend.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "";

// ---------------------------------------------------------------------------
// Types — these mirror the Pydantic schemas on the backend
// ---------------------------------------------------------------------------
// In a production setup, you'd auto-generate these from the OpenAPI spec.
// For now, we define them manually to match backend/src/hts_oracle/schemas/classify.py.

export interface HtsResult {
  hts_code: string;
  description: string;
  general_rate: string;
  special_rate: string;
  unit: string;
  chapter: string;
  context_path: string;
  confidence_score: number;  // 0-100
  similarity: number;        // 0-1
}

export interface ClassifyResponse {
  results: HtsResult[];
  method: "vector_only" | "llm_assisted";
  analysis: string | null;
  latency_ms: number;
}

export interface ClassifyRequest {
  query: string;
  material?: string;
  intended_use?: string;
  form?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Classify a product description into HTS codes.
 *
 * This is the main API call. It sends the user's query (and optional
 * refinement fields) to the backend classifier.
 *
 * Throws an Error with a user-friendly message if the request fails.
 */
export async function classifyProduct(
  request: ClassifyRequest
): Promise<ClassifyResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/classify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    // Try to extract an error message from the response body
    const error = await response.json().catch(() => ({}));
    throw new Error(
      (error as Record<string, string>).detail ??
        `Classification failed (${response.status})`
    );
  }

  return response.json();
}

/**
 * Health check — verify the backend is running.
 */
export async function checkHealth(): Promise<{ status: string; version: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`);
  if (!response.ok) throw new Error("Backend is not responding");
  return response.json();
}