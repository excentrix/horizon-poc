// frontend/src/components/sidebar.tsx
"use client";

import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

const scenarios = [
  { id: "1", title: "Career Guidance", active: true },
  { id: "2", title: "Study Planning", active: false },
  { id: "3", title: "Skill Assessment", active: false },
  { id: "4", title: "Interview Prep", active: false },
];

export function SideBar() {
  return (
    <div className="p-4 h-full flex flex-col">
      {/* Avatar Card */}
      <Card className="p-4 mb-6 bg-mint/10 border-mint/20">
        <div className="flex items-center space-x-3">
          <Avatar className="h-12 w-12">
            <AvatarImage src="/avatar.png" />
            <AvatarFallback className="bg-mint text-dark font-semibold">
              HZ
            </AvatarFallback>
          </Avatar>
          <div>
            <h3 className="font-semibold text-white">Horizon AI</h3>
            <p className="text-sm text-gray1">Your Learning Mentor</p>
          </div>
        </div>
      </Card>

      {/* Scenarios List */}
      <div className="flex-1">
        <h4 className="text-sm font-medium text-gray1 mb-3 uppercase tracking-wide">
          Learning Scenarios
        </h4>
        <div className="space-y-2">
          {scenarios.map((scenario) => (
            <div
              key={scenario.id}
              className={`p-3 rounded-lg cursor-pointer transition-all duration-200 ${
                scenario.active
                  ? "bg-mint/20 border border-mint/30"
                  : "hover:bg-gray2/10"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{scenario.title}</span>
                {scenario.active && (
                  <Badge
                    variant="secondary"
                    className="bg-mint text-dark text-xs"
                  >
                    Active
                  </Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
