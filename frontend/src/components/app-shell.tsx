// frontend/src/components/app-shell.tsx
"use client";

import { useState } from "react";
import { SideBar } from "./sidebar";
import { ChatArea } from "./chat/chat-area";
import { UserInfoPanel } from "./panels/user-info-panel";
import { SessionsPanel } from "./panels/sessions-panel";
import { ErrorBoundary } from "./error-boundary";
import { useFacts } from "@/hooks/use-facts";
import { useSession } from "next-auth/react";

export function AppShell() {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const { data: session } = useSession();
  const { data: facts, isLoading, error } = useFacts();

  return (
    <div className="h-screen bg-dark text-white">
      <div className="h-full lg:grid lg:grid-cols-[260px_1fr_260px] lg:grid-rows-[auto_1fr_auto]">
        {/* Sidebar */}
        <div className="hidden lg:block lg:row-span-full border-r border-gray2/20">
          <ErrorBoundary>
            <SideBar />
          </ErrorBoundary>
        </div>

        {/* Main Chat Area */}
        <div className="hidden lg:block lg:row-span-full border-l border-gray2/20 bg-dark/50">
          <ErrorBoundary>
            <ChatArea
              sessionId={currentSessionId}
              onSessionChange={setCurrentSessionId}
            />
          </ErrorBoundary>
        </div>

        {/* Right Panel */}
        <div className="flex flex-col h-full">
          <div className="p-4 space-y-4 h-full overflow-y-auto">
            <ErrorBoundary>
              <UserInfoPanel facts={facts} isLoading={isLoading} />
            </ErrorBoundary>
            <ErrorBoundary>
              <SessionsPanel
                sessions={facts?.sessions || []}
                onSessionSelect={setCurrentSessionId}
              />
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </div>
  );
}
