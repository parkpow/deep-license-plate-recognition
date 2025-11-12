"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/header";
import { Layout } from "@/components/layout";
import { LicensePlateSidebar } from "@/components/license-plate-sidebar";
import { LastVehicleDetails } from "@/components/last-vehicle-details";
import { DashboardSummary } from "@/components/dashboard-summary";
import { EmptyState } from "@/components/empty-state";
import type { WebhookData } from "@/types/webhook";
import { useToast } from "@/hooks/use-toast";
import { useParams, useRouter } from "next/navigation";
import { Copy, Trash } from "lucide-react";

export default function WebhookDataPage() {
  const params = useParams();
  const uuid = params?.uuid as string;

  const [webhookData, setWebhookData] = useState<WebhookData[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const { toast } = useToast();
  const router = useRouter();
  const [baseUrl, setBaseUrl] = useState("");

  // Set base URL on client side
  useEffect(() => {
    setBaseUrl(window.location.origin);
  }, []);

  // Fetch data on page load
  useEffect(() => {
    if (!uuid) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const url = `/api/webhook/${uuid}`;
        const response = await fetch(url);

        if (!response.ok) {
          if (response.status === 404) {
            toast({
              title: "Webhook Not Found",
              description: "The webhook you're looking for doesn't exist",
              variant: "destructive",
            });
            router.push("/");
            return;
          } else if (response.status === 400) {
            toast({
              title: "Invalid UUID",
              description: "The UUID you provided is invalid",
              variant: "destructive",
            });
            router.push("/");
            return;
          }

          toast({
            title: "Error",
            description: `Failed to fetch data: ${response.statusText}`,
            variant: "destructive",
          });
          return;
        }

        const data = await response.json();
        if (data.length >= process.env.NEXT_PUBLIC_MAX_WEBHOOK_REQUESTS) {
          toast({
            title: "Webhook Limit Reached",
            description:
              "You have reached the maximum number of requests for this webhook",
            variant: "destructive",
          });
        }

        if (Array.isArray(data) && data.length > 0) {
          console.log("Received data:", data.length, "items");
          setWebhookData(data);
        } else {
          setWebhookData([]);
        }
      } catch (error) {
        console.error("Error fetching webhook data:", error);
        toast({
          title: "Error",
          description: "Failed to fetch webhook data",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    // Fetch initial data
    fetchData();

    // Set up polling for real-time updates
    const intervalId = setInterval(fetchData, 5000);

    return () => clearInterval(intervalId);
  }, [uuid, toast, router]);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/webhook/${uuid}`);
      if (response.ok) {
        const data = await response.json();
        setWebhookData(data);
        toast({
          title: "Data Refreshed",
          description: `Found ${data.length} records`,
        });
      }
    } catch (error) {
      console.error("Error refreshing data:", error);
      toast({
        title: "Refresh Failed",
        description: "Could not refresh data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDataClear = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/webhook/${uuid}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setWebhookData([]);
        toast({
          title: "Data Cleared",
          description: "All webhook data has been cleared",
        });
      } else {
        toast({
          title: "Error",
          description: "Failed to clear data",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error clearing data:", error);
      toast({
        title: "Error",
        description: "Failed to clear data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const testApiConnection = async () => {
    try {
      setLoading(true);

      // First test a simple endpoint
      const testResponse = await fetch("/api/webhook/test", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ test: "data" }),
      });

      if (testResponse.ok) {
        // toast({
        //   title: "Test API Connection Successful",
        //   description: "The API is responding correctly",
        // });

        // Now test sending some sample data to our webhook
        const sampleData = {
          data: {
            camera_id: "test-camera",
            filename: "test.jpg",
            results: [
              {
                plate: "ABC1D23",
                box: { xmin: 0, ymin: 0, xmax: 100, ymax: 50 },
                vehicle: {
                  type: "Car",
                  box: { xmin: 0, ymin: 0, xmax: 200, ymax: 150 },
                  score: 0.95,
                },
                color: [{ color: "black", score: 0.9 }],
                model_make: [{ make: "Test", model: "Model", score: 0.8 }],
                direction: 90,
                speed: 60,
                score: 0.95,
                source_url: "test-url",
              },
            ],
            timestamp: new Date().toISOString(),
            timestamp_local: new Date().toISOString(),
            timestamp_camera: new Date().toISOString(),
          },
          hook: {
            event: "test",
            filename: "test.jpg",
            id: "test-id",
            target: `/api/webhook/${uuid}`,
          },
          receivedAt: new Date().toISOString(),
        };

        const webhookResponse = await fetch(`/api/webhook/${uuid}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(sampleData),
        });

        if (webhookResponse.ok) {
          toast({
            title: "Test Data Sent Successfully",
            description:
              "Sample license plate data has been sent to your webhook",
          });

          // Refresh to show the test data
          handleRefresh();
        }
      } else {
        toast({
          title: "API Connection Failed",
          description: `Status: ${testResponse.status} ${testResponse.statusText}`,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error testing API connection:", error);
      toast({
        title: "API Connection Error",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Get the latest vehicle data
  const latestVehicle =
    webhookData.length > 0
      ? webhookData.sort((a, b) => {
          const timeA = a.receivedAt ? new Date(a.receivedAt).getTime() : 0;
          const timeB = b.receivedAt ? new Date(b.receivedAt).getTime() : 0;
          return timeB - timeA;
        })[0]
      : null;

  return (
    <Layout
      header={<Header />}
      sidebar={
        <LicensePlateSidebar
          data={webhookData}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
        />
      }
      main={
        <div className="space-y-4 overflow-auto">
          {/* Dashboard Summary at the top */}
          <DashboardSummary
            data={webhookData}
            onRefresh={handleRefresh}
            onTestData={testApiConnection}
            loading={loading}
          />

          {/* Webhook URL Display */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Webhook URL</h2>
            <div className="flex items-center gap-2">
              <div className="bg-gray-100 h-10 px-3 flex items-center rounded flex-1 font-mono text-sm overflow-x-auto">
                {baseUrl ? `${baseUrl}/api/webhook/${uuid}` : `Loading...`}
              </div>
              <button
                onClick={() => {
                  if (baseUrl) {
                    navigator.clipboard.writeText(
                      `${baseUrl}/api/webhook/${uuid}`,
                    );
                    toast({
                      title: "Copy!",
                      description:
                        "URL of the webhook copied to the clipboard.",
                    });
                  }
                }}
                className="h-10 w-10 flex items-center justify-center bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                title="Copiar URL"
              >
                <Copy className="w-4 h-4" />
              </button>
              <button
                onClick={handleDataClear}
                className="h-10 w-10 flex items-center justify-center bg-red-100 text-red-600 rounded hover:bg-red-200 transition-colors"
                title="Limpar Dados"
              >
                <Trash className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Main content area */}
          {loading && webhookData.length === 0 ? (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
              <span className="ml-2">Loading data...</span>
            </div>
          ) : webhookData.length === 0 ? (
            <EmptyState uuid={uuid} />
          ) : (
            <div className="space-y-4">
              {/* Latest vehicle details */}
              {latestVehicle && <LastVehicleDetails data={latestVehicle} />}
            </div>
          )}
        </div>
      }
    />
  );
}
