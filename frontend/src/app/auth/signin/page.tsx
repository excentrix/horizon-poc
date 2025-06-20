// frontend/src/app/auth/signin/page.tsx
"use client";

import { useState } from "react";
import { signIn, getProviders } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Github, Mail } from "lucide-react";
import { FaGoogle } from "react-icons/fa";
import { useEffect } from "react";

export default function SignInPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [providers, setProviders] = useState<any>({});
  const router = useRouter();

  useEffect(() => {
    getProviders()
      .then((fetchedProviders) => {
        setProviders(fetchedProviders);
      })
      .catch((err) => {
        console.error("Failed to fetch providers:", err);
        setError("Failed to load authentication providers");
      });
  }, []);

  const handleOAuthSignIn = async (providerId: string) => {
    setIsLoading(true);
    setError("");

    try {
      const result = await signIn(providerId, {
        callbackUrl: "/",
        redirect: false,
      });

      if (result?.error) {
        setError(`Failed to sign in with ${providerId}`);
      } else if (result?.url) {
        router.push(result.url);
      }
    } catch (err) {
      setError("An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const getProviderIcon = (providerId: string) => {
    switch (providerId) {
      case "github":
        return <Github className="h-4 w-4 mr-2" />;
      case "google":
        return <FaGoogle className="h-4 w-4 mr-2" />;
      case "email":
        return <Mail className="h-4 w-4 mr-2" />;
      default:
        return null;
    }
  };

  const getProviderStyle = (providerId: string) => {
    switch (providerId) {
      case "github":
        return "bg-mint hover:bg-mint/80 text-dark font-medium";
      case "google":
        return "bg-white hover:bg-gray-100 text-gray-900 font-medium border border-gray-300";
      default:
        return "bg-gray-600 hover:bg-gray-700 text-white";
    }
  };

  return (
    <div className="min-h-screen bg-dark flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-gray2/10 border-gray2/20">
        <CardHeader className="text-center">
          <CardTitle className="text-white text-2xl">
            Welcome to Horizon
          </CardTitle>
          <CardDescription className="text-gray1">
            Sign in to your AI learning mentor
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* OAuth Providers */}
          <div className="space-y-3">
            {Object.values(providers).map((provider: any) => (
              <Button
                key={provider.id}
                onClick={() => handleOAuthSignIn(provider.id)}
                disabled={isLoading}
                className={`w-full ${getProviderStyle(provider.id)}`}
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  getProviderIcon(provider.id)
                )}
                Continue with {provider.name}
              </Button>
            ))}
          </div>

          <p className="text-xs text-gray1 text-center">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
