/**
 * AdminPage — database stats and management.
 *
 * Shows how many HTS codes are in the database, how many have embeddings,
 * and provides a link to run the import CLI command.
 *
 * For now this is read-only. CSV import is done via the CLI command
 * (python -m hts_oracle.cli.import_hts) because it takes several minutes
 * and is better run in a terminal where you can see progress.
 */

import { useQuery } from "@tanstack/react-query";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "";

interface Stats {
  total_codes: number;
  with_embeddings: number;
  without_embeddings: number;
}

async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export function AdminPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: fetchStats,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Admin</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Database stats and management.
        </p>
      </div>

      {/* Stats cards */}
      {isLoading && (
        <p className="text-sm text-muted-foreground">Loading stats...</p>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
          Could not connect to backend. Is the server running?
        </div>
      )}

      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Total HTS Codes" value={data.total_codes} />
          <StatCard
            label="With Embeddings"
            value={data.with_embeddings}
            color="text-green-600"
          />
          <StatCard
            label="Missing Embeddings"
            value={data.without_embeddings}
            color={data.without_embeddings > 0 ? "text-yellow-600" : "text-green-600"}
          />
        </div>
      )}

      {/* Import instructions */}
      <div className="rounded-xl border bg-muted/30 p-4 space-y-2">
        <p className="text-sm font-medium">Import HTS Data</p>
        <p className="text-sm text-muted-foreground">
          To import or update HTS codes, run this command from the backend directory:
        </p>
        <code className="block bg-background border rounded-lg px-3 py-2 text-sm font-mono">
          python -m hts_oracle.cli.import_hts ../data/hts_2026_revision_4_enriched.csv
        </code>
        <p className="text-xs text-muted-foreground">
          Safe to re-run — existing codes are updated, not duplicated.
        </p>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div className="rounded-xl border bg-background p-4 text-center">
      <p className={`text-3xl font-bold ${color ?? ""}`}>
        {value.toLocaleString()}
      </p>
      <p className="text-sm text-muted-foreground mt-1">{label}</p>
    </div>
  );
}
