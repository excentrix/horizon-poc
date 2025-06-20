// frontend/src/app/auth/error/page.tsx
"use client";

import { useSearchParams } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";
import Link from "next/link";

export default function AuthError() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");

  const getErrorMessage = (error: string | null) => {
    switch (error) {
      case "Configuration":
        return "There is a problem with the server configuration.";
      case "AccessDenied":
        return "Access was denied. Please try again.";
      case "Verification":
        return "The verification link is invalid or has expired.";
      default:
        return "An error occurred during authentication.";
    }
  };

  return (
    <div className="min-h-screen bg-dark flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-gray2/10 border-gray2/20">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
            <AlertTriangle className="h-6 w-6 text-red-600" />
          </div>
          <CardTitle className="text-white">Authentication Error</CardTitle>
          <CardDescription className="text-gray1">
            {getErrorMessage(error)}
          </CardDescription>
        </CardHeader>

        <CardContent className="text-center">
          <Link href="/auth/signin">
            <Button className="w-full bg-mint hover:bg-mint/80 text-dark">
              Try Again
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
