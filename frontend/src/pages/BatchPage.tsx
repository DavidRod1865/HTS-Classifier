/**
 * BatchPage — PDF invoice upload and batch classification.
 *
 * Flow:
 *   1. User drops a PDF on the UploadZone
 *   2. We upload it → get a job_id
 *   3. Connect to SSE stream for that job
 *   4. ProgressTable fills in as items are classified
 *   5. When complete, show summary + full results table
 *
 * State is managed with useReducer (not multiple useState hooks like v1).
 * This makes the state transitions explicit and prevents impossible states
 * (e.g., "loading but also has results" or "error but still processing").
 */

import { useReducer, useCallback, useRef, useEffect } from "react";
import { UploadZone } from "@/components/batch/UploadZone";
import { ProgressTable } from "@/components/batch/ProgressTable";
import { uploadPdf, streamBatchProgress, type BatchItem, type BatchSummary, type BatchSSEEvent } from "@/api/batch";

// ---------------------------------------------------------------------------
// State management — useReducer instead of 5 separate useState hooks
// ---------------------------------------------------------------------------

interface BatchState {
  status: "idle" | "uploading" | "processing" | "complete" | "error";
  phase: string;
  progress: number;
  items: BatchItem[];
  summary: BatchSummary | null;
  error: string | null;
  jobId: number | null;
}

const initialState: BatchState = {
  status: "idle",
  phase: "",
  progress: 0,
  items: [],
  summary: null,
  error: null,
  jobId: null,
};

type BatchAction =
  | { type: "UPLOAD_START" }
  | { type: "UPLOAD_DONE"; jobId: number }
  | { type: "PHASE"; phase: string; progress: number }
  | { type: "ITEM"; item: BatchItem }
  | { type: "COMPLETE"; items: BatchItem[]; summary: BatchSummary }
  | { type: "ERROR"; message: string }
  | { type: "RESET" };

function batchReducer(state: BatchState, action: BatchAction): BatchState {
  switch (action.type) {
    case "UPLOAD_START":
      return { ...initialState, status: "uploading" };
    case "UPLOAD_DONE":
      return { ...state, status: "processing", jobId: action.jobId };
    case "PHASE":
      return { ...state, phase: action.phase, progress: action.progress };
    case "ITEM":
      return { ...state, items: [...state.items, action.item] };
    case "COMPLETE":
      return { ...state, status: "complete", items: action.items, summary: action.summary, progress: 100 };
    case "ERROR":
      return { ...state, status: "error", error: action.message };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BatchPage() {
  const [state, dispatch] = useReducer(batchReducer, initialState);

  // Keep a ref to the SSE abort controller so we can disconnect on unmount
  const abortRef = useRef<AbortController | null>(null);

  // Clean up SSE connection when leaving the page
  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  // Handle SSE events from the batch stream
  const handleEvent = useCallback((event: BatchSSEEvent) => {
    switch (event.event) {
      case "phase":
        dispatch({ type: "PHASE", phase: event.phase, progress: event.progress });
        break;
      case "item_progress":
        if (event.status !== "searching") {
          dispatch({
            type: "ITEM",
            item: {
              commodity: event.commodity,
              hts_code: event.hts_code ?? "",
              description: "",
              confidence: event.confidence ?? 0,
              general_rate: "",
              status: event.status as BatchItem["status"],
            },
          });
        }
        break;
      case "complete":
        dispatch({ type: "COMPLETE", items: event.items, summary: event.summary });
        break;
      case "error":
        dispatch({ type: "ERROR", message: event.message });
        break;
    }
  }, []);

  // Upload PDF and start streaming
  const handleUpload = useCallback(async (file: File) => {
    dispatch({ type: "UPLOAD_START" });

    try {
      // Step 1: Upload the PDF
      const { job_id } = await uploadPdf(file);
      dispatch({ type: "UPLOAD_DONE", jobId: job_id });

      // Step 2: Connect to SSE stream
      const controller = streamBatchProgress(
        job_id,
        handleEvent,
        (error) => dispatch({ type: "ERROR", message: error.message }),
      );
      abortRef.current = controller;
    } catch (err) {
      dispatch({ type: "ERROR", message: (err as Error).message });
    }
  }, [handleEvent]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Batch Classification</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload a PDF invoice to classify all products at once.
        </p>
      </div>

      {/* Show upload zone when idle or errored */}
      {(state.status === "idle" || state.status === "error") && (
        <>
          <UploadZone
            onUpload={handleUpload}
            isLoading={state.status === "uploading"}
          />
          {state.error && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
              <p className="font-medium">Error</p>
              <p className="mt-1">{state.error}</p>
            </div>
          )}
        </>
      )}

      {/* Show progress when uploading/processing */}
      {(state.status === "uploading") && (
        <div className="text-center py-8 text-muted-foreground">
          Uploading PDF...
        </div>
      )}

      {/* Show progress table when processing or complete */}
      {(state.status === "processing" || state.status === "complete") && (
        <ProgressTable
          phase={state.phase}
          progress={state.progress}
          items={state.items}
          summary={state.summary}
          isComplete={state.status === "complete"}
        />
      )}

      {/* New batch button when complete */}
      {state.status === "complete" && (
        <button
          onClick={() => dispatch({ type: "RESET" })}
          className="px-4 py-2 text-sm font-medium rounded-lg border hover:bg-muted transition-colors"
        >
          Upload another PDF
        </button>
      )}
    </div>
  );
}