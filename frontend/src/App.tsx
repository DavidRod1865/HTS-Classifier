/**
 * Root component — routing and layout.
 *
 * In v1, App.jsx held ALL state (10+ useState hooks) and all API logic.
 * In v2, App.tsx is just a router. State and data fetching live in
 * individual page components via TanStack Query hooks.
 *
 * Three routes:
 *   /       → SearchPage  (single product classification)
 *   /batch  → BatchPage   (PDF invoice upload + batch classification)
 *   /admin  → AdminPage   (CSV data management)
 */

import { Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { SearchPage } from "@/pages/SearchPage";
import { BatchPage } from "@/pages/BatchPage";
import { AdminPage } from "@/pages/AdminPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/batch" element={<BatchPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </AppShell>
  );
}