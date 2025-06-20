// frontend/src/components/error-boundary.tsx
"use client";

import React from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw } from "lucide-react";

// Extend the Window interface to include Sentry
declare global {
  interface Window {
    Sentry?: {
      captureException: (error: Error) => void;
    };
  }
}

interface Props {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; reset: () => void }>;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);

    // Log to Sentry if available
    if (typeof window !== "undefined" && window.Sentry) {
      window.Sentry.captureException(error);
    }
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return (
          <this.props.fallback error={this.state.error!} reset={this.reset} />
        );
      }

      return (
        <div className="p-4 h-full flex items-center justify-center">
          <Alert variant="destructive" className="max-w-lg">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Something went wrong</AlertTitle>
            <AlertDescription className="mt-2">
              <p className="mb-4">
                We encountered an unexpected error. Our team has been notified.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={this.reset}
                className="bg-destructive/10 hover:bg-destructive/20"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}
