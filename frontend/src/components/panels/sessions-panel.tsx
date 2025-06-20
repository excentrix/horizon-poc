// frontend/src/components/panels/sessions-panel.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { History, MessageCircle } from "lucide-react";

interface Session {
  id: string;
  summary: string;
  created_at: string;
}

interface SessionsPanelProps {
  sessions: Session[];
  onSessionSelect: (sessionId: string) => void;
}

export function SessionsPanel({
  sessions,
  onSessionSelect,
}: SessionsPanelProps) {
  return (
    <Card className="bg-mist/10 border-mist/20">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <History className="h-4 w-4" />
          Recent Sessions
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-48">
          <div className="space-y-2">
            {sessions.length === 0 ? (
              <p className="text-sm text-gray1 text-center py-4">
                No previous sessions
              </p>
            ) : (
              sessions.map((session) => (
                <Button
                  key={session.id}
                  variant="ghost"
                  className="w-full justify-start text-left h-auto p-3 hover:bg-mist/10"
                  onClick={() => onSessionSelect(session.id)}
                >
                  <div className="flex items-start gap-2 w-full">
                    <MessageCircle className="h-4 w-4 mt-0.5 text-mist flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white line-clamp-2">
                        {session.summary}
                      </p>
                      <p className="text-xs text-gray1 mt-1">
                        {new Date(session.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </Button>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
