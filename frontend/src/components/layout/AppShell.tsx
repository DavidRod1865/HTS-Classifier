/**
 * AppShell — wraps every page with a consistent header and layout.
 *
 * This is the outer frame of the app: header at the top, content below.
 * Every page (Search, Batch, Admin) renders inside this shell.
 */

import { Header } from "./Header";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      {/* Main content area — grows to fill available space */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}