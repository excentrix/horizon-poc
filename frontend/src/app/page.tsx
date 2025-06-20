// frontend/src/app/page.tsx
"use client";

import { AppShell } from "@/components/app-shell";
import { ProtectedRoute } from "@/components/auth/protected-route";

export default function HomePage() {
  return (
    <ProtectedRoute>
      <AppShell />
    </ProtectedRoute>
  );
}
