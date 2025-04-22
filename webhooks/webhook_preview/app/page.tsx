"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { generateUUID } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

export default function HomePage() {
  const [uuid, setUuid] = useState<string>("");
  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    // Generate a UUID if none exists
    setUuid(generateUUID());
  }, []);

  const handleCreateWebhook = async () => {
    const uuidRegex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

    if (!uuidRegex.test(uuid)) {
      toast({
        title: "Invalid UUID",
        description: "Please use the generated UUID or generate a new one",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await fetch("/api/new-webhook/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ uuid }),
      });

      if (!response.ok) {
        throw new Error("Failed to create webhook");
      }

      const data = await response.json();

      if (data?.success) {
        router.push(`/${uuid}`);
      } else {
        toast({
          title: "Error",
          description: "Webhook could not be created",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Something went wrong",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>License Plate Recognition Dashboard</CardTitle>
          <CardDescription>
            Create a new webhook URL to receive license plate recognition data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="uuid" className="text-sm font-medium">
                Webhook UUID
              </label>
              <Input
                id="uuid"
                value={uuid}
                readOnly
                placeholder="Generated UUID"
                className="font-mono"
              />
              <p className="text-xs text-muted-foreground">
                This UUID will be used to access your webhook data
              </p>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={() => setUuid(generateUUID())}>
            Generate New UUID
          </Button>
          <Button onClick={handleCreateWebhook}>Create Webhook</Button>
        </CardFooter>
      </Card>
    </div>
  );
}
