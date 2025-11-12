"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import type { WebhookData } from "@/types/webhook";

interface DashboardSummaryProps {
  data: WebhookData[];
  onRefresh: () => void;
  onTestData: () => void;
  loading: boolean;
}

export function DashboardSummary({
  data,
  onRefresh,
  onTestData,
  loading,
}: DashboardSummaryProps) {
  const uniquePlates = new Set(
    data
      .map((item) => {
        const plateNumber = item.data?.results?.[0]?.plate;
        if (typeof plateNumber === "string") {
          return plateNumber;
        } else if (plateNumber?.props?.plate?.[0]?.value) {
          return plateNumber.props.plate[0].value;
        }
        return null;
      })
      .filter(Boolean),
  ).size;

  // Get last detection time
  const lastDetection =
    data.length > 0
      ? new Date(
          data.sort((a, b) => {
            const timeA = a.receivedAt ? new Date(a.receivedAt).getTime() : 0;
            const timeB = b.receivedAt ? new Date(b.receivedAt).getTime() : 0;
            return timeB - timeA;
          })[0].receivedAt || "",
        ).toLocaleTimeString()
      : "N/A";

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Dashboard Summary</h2>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={loading}
            >
              <RefreshCw
                className={`h-3 w-3 mr-1 ${loading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onTestData}
              disabled={loading}
            >
              Test API
            </Button>
          </div>
        </div>

        <div className="flex gap-4">
          <div className="flex-1 bg-blue-50 p-3 rounded-lg">
            <div className="text-xs text-blue-600 font-medium">
              Total Plates
            </div>
            <div className="text-xl font-bold">{data.length}</div>
          </div>
          <div className="flex-1 bg-green-50 p-3 rounded-lg">
            <div className="text-xs text-green-600 font-medium">
              Unique Plates
            </div>
            <div className="text-xl font-bold">{uniquePlates}</div>
          </div>
          <div className="flex-1 bg-purple-50 p-3 rounded-lg">
            <div className="text-xs text-purple-600 font-medium">
              Last Detection
            </div>
            <div className="text-xl font-bold truncate">{lastDetection}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
