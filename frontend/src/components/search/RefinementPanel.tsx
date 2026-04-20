/**
 * RefinementPanel — optional fields to narrow down ambiguous results.
 *
 * In v1, disambiguation happened via chat (Claude asks "is it knitted or woven?").
 * In v2, the user can proactively provide this info via a simple form.
 *
 * This panel appears AFTER the first search, below the results.
 * It's collapsible — most users won't need it because vector search
 * is confident enough. But when it's not, these fields help without
 * needing a Claude call.
 *
 * The three fields map to the most common disambiguation axes in HTS:
 *   - Material: "cotton" vs "polyester" vs "steel" changes the code
 *   - Intended use: "retail" vs "industrial" vs "medical"
 *   - Form: "knitted" vs "woven" vs "sheet" vs "pipe"
 */

import { cn } from "@/lib/utils";

interface Refinements {
  material: string;
  intended_use: string;
  form: string;
}

interface RefinementPanelProps {
  values: Refinements;
  onChange: (values: Refinements) => void;
  onRefine: () => void;
  isLoading: boolean;
}

export function RefinementPanel({
  values,
  onChange,
  onRefine,
  isLoading,
}: RefinementPanelProps) {
  // Check if any refinement field has been filled in
  const hasRefinements = Object.values(values).some((v) => v.trim());

  return (
    <div className="rounded-xl border bg-muted/30 p-4 space-y-3">
      <p className="text-sm font-medium text-muted-foreground">
        Refine your search (optional)
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Material field */}
        <div>
          <label htmlFor="material" className="text-xs font-medium text-muted-foreground">
            Material
          </label>
          <input
            id="material"
            type="text"
            value={values.material}
            onChange={(e) => onChange({ ...values, material: e.target.value })}
            placeholder="e.g., cotton, steel"
            className={cn(
              "mt-1 w-full rounded-lg border bg-background px-3 py-2 text-sm",
              "placeholder:text-muted-foreground/50",
              "focus:outline-none focus:ring-1 focus:ring-primary/30"
            )}
          />
        </div>

        {/* Intended use field */}
        <div>
          <label htmlFor="intended_use" className="text-xs font-medium text-muted-foreground">
            Intended Use
          </label>
          <input
            id="intended_use"
            type="text"
            value={values.intended_use}
            onChange={(e) => onChange({ ...values, intended_use: e.target.value })}
            placeholder="e.g., retail, industrial"
            className={cn(
              "mt-1 w-full rounded-lg border bg-background px-3 py-2 text-sm",
              "placeholder:text-muted-foreground/50",
              "focus:outline-none focus:ring-1 focus:ring-primary/30"
            )}
          />
        </div>

        {/* Form field */}
        <div>
          <label htmlFor="form" className="text-xs font-medium text-muted-foreground">
            Form / Shape
          </label>
          <input
            id="form"
            type="text"
            value={values.form}
            onChange={(e) => onChange({ ...values, form: e.target.value })}
            placeholder="e.g., knitted, woven"
            className={cn(
              "mt-1 w-full rounded-lg border bg-background px-3 py-2 text-sm",
              "placeholder:text-muted-foreground/50",
              "focus:outline-none focus:ring-1 focus:ring-primary/30"
            )}
          />
        </div>
      </div>

      {/* Refine button — only active when at least one field is filled */}
      {hasRefinements && (
        <button
          onClick={onRefine}
          disabled={isLoading}
          className={cn(
            "mt-2 px-4 py-2 text-sm font-medium rounded-lg",
            "bg-primary text-primary-foreground",
            "hover:bg-primary/90 transition-colors",
            "disabled:opacity-50"
          )}
        >
          {isLoading ? "Searching..." : "Refine Search"}
        </button>
      )}
    </div>
  );
}