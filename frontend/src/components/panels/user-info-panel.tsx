// frontend/src/components/panels/user-info-panel.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { User, BookOpen, Target } from "lucide-react";

interface UserInfoPanelProps {
  facts: any;
  isLoading: boolean;
}

export function UserInfoPanel({ facts, isLoading }: UserInfoPanelProps) {
  if (isLoading) {
    return (
      <Card className="bg-mint/10 border-mint/20">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <User className="h-4 w-4" />
            User Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-full bg-gray2/20" />
          <Skeleton className="h-4 w-3/4 bg-gray2/20" />
          <Skeleton className="h-4 w-1/2 bg-gray2/20" />
        </CardContent>
      </Card>
    );
  }

  const profile = facts?.profile || {};

  return (
    <Card className="bg-mint/10 border-mint/20">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <User className="h-4 w-4" />
          User Profile
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {profile.name && (
          <div>
            <span className="text-sm text-gray1">Name</span>
            <p className="text-white font-medium">{profile.name}</p>
          </div>
        )}

        {profile.degree && (
          <div>
            <span className="text-sm text-gray1">Degree</span>
            <p className="text-white font-medium">{profile.degree}</p>
          </div>
        )}

        {profile.year && (
          <div>
            <span className="text-sm text-gray1">Year</span>
            <Badge variant="secondary" className="bg-mint text-dark">
              Year {profile.year}
            </Badge>
          </div>
        )}

        {profile.goal && (
          <div>
            <span className="text-sm text-gray1 flex items-center gap-1">
              <Target className="h-3 w-3" />
              Career Goal
            </span>
            <p className="text-white text-sm leading-relaxed">{profile.goal}</p>
          </div>
        )}

        {profile.fav_subject && (
          <div>
            <span className="text-sm text-gray1 flex items-center gap-1">
              <BookOpen className="h-3 w-3" />
              Favorite Subject
            </span>
            <Badge variant="outline" className="border-mist text-mist">
              {profile.fav_subject}
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
