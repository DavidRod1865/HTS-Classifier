/**
 * Utility: cn() — merge Tailwind classes safely.
 *
 * Combines clsx (conditional classes) with tailwind-merge (deduplication).
 *
 * Why do we need this?
 *   <div className={cn("px-4 py-2", isActive && "bg-blue-500", className)} />
 *
 * Without tailwind-merge, if className contains "px-8", you'd end up with
 * both "px-4" and "px-8" — and Tailwind's last-class-wins behavior is
 * unpredictable. tailwind-merge resolves conflicts correctly.
 *
 * This is the standard pattern used by shadcn/ui components.
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}