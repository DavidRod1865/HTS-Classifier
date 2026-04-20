/**
 * Batch API client — handles PDF upload and SSE streaming.
 *
 * The batch flow is two steps:
 *   1. Upload PDF → get a job_id
 *   2. Connect to SSE stream → receive real-time progress events
 *
 * This module provides typed functions for both steps, plus a typed
 * event parser for the SSE stream.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "";

// ---------------------------------------------------------------------------
// Types for SSE events (mirrors backend/schemas/batch.py)
// ---------------------------------------------------------------------------

export interface PhaseEvent {
  event: "phase";
  phase: string;
  progress: number;
  total: number;
}

export interface ItemProgressEvent {
  event: "item_progress";
  index: number;
  total: number;
  commodity: string;
  status: "searching" | "confident" | "ambiguous" | "needs_review";
  hts_code?: string;
  confidence?: number;
}

export interface CompleteEvent {
  event: "complete";
  items: BatchItem[];
  summary: BatchSummary;
}

export interface ErrorEvent {
  event: "error";
  message: string;
}

export type BatchSSEEvent = PhaseEvent | ItemProgressEvent | CompleteEvent | ErrorEvent;

export interface BatchItem {
  commodity: string;
  quantity?: string;
  value?: string;
  hts_code: string;
  description: string;
  confidence: number;
  general_rate: string;
  status: "confident" | "ambiguous" | "llm_assisted" | "needs_review";
}

export interface BatchSummary {
  total: number;
  classified: number;
  needs_review: number;
  avg_confidence: number;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Upload a PDF for batch classification. Returns a job_id.
 */
export async function uploadPdf(file: File): Promise<{ job_id: number; filename: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/v1/batch/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error((error as Record<string, string>).detail ?? `Upload failed (${response.status})`);
  }

  return response.json();
}

/**
 * Connect to the SSE stream for a batch job.
 *
 * This is the SSE client. It reads the stream and calls the onEvent
 * callback for each parsed event. The callback receives typed events
 * so the component doesn't need to do any parsing.
 *
 * Returns an AbortController — call .abort() to disconnect.
 */
export function streamBatchProgress(
  jobId: number,
  onEvent: (event: BatchSSEEvent) => void,
  onError: (error: Error) => void,
): AbortController {
  const controller = new AbortController();

  // Use fetch + ReadableStream instead of EventSource.
  // EventSource doesn't support custom headers or POST requests,
  // and it auto-reconnects in ways we don't want to handle here.
  (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/batch/${jobId}/stream`, {
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Stream connection failed (${response.status})`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE events are separated by double newlines
        const parts = buffer.split("\n\n");
        buffer = parts.pop()!; // Keep incomplete chunk

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;

          try {
            const event = JSON.parse(line.slice(6)) as BatchSSEEvent;
            onEvent(event);
          } catch {
            // Skip malformed events
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onError(err as Error);
      }
    }
  })();

  return controller;
}