/**
 * Header — top navigation bar.
 *
 * Shows the app name and navigation links. Uses React Router's NavLink
 * for active-state highlighting (the current page link is underlined).
 */

import { NavLink } from "react-router-dom";
import { Search, FileUp, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

// Helper: style for nav links. Active link gets an underline.
function navLinkClass({ isActive }: { isActive: boolean }) {
  return cn(
    "flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
    isActive
      ? "text-primary bg-accent"
      : "text-muted-foreground hover:text-foreground hover:bg-muted"
  );
}

export function Header() {
  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-5xl mx-auto px-4 flex items-center justify-between h-14">
        {/* Logo / app name */}
        <NavLink to="/" className="text-lg font-bold tracking-tight">
          HTS Oracle
        </NavLink>

        {/* Navigation links */}
        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={navLinkClass}>
            <Search className="w-4 h-4" />
            Search
          </NavLink>
          <NavLink to="/batch" className={navLinkClass}>
            <FileUp className="w-4 h-4" />
            Batch
          </NavLink>
          <NavLink to="/admin" className={navLinkClass}>
            <Settings className="w-4 h-4" />
            Admin
          </NavLink>
        </nav>
      </div>
    </header>
  );
}