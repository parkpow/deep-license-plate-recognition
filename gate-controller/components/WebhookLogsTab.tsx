"use client";

import { type Event, listen } from "@tauri-apps/api/event";
import { CheckCircle2, Trash2, XCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface WebhookLog {
  timestamp: string;
  success: boolean;
  details: string;
  error_message: string | null;
}

export function WebhookLogsTab() {
  const [logs, setLogs] = useState<WebhookLog[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const shouldScrollRef = useRef(false);

  useEffect(() => {
    const unlisten = listen<WebhookLog>("webhook-log", (event: Event<WebhookLog>) => {
      setLogs((prevLogs: WebhookLog[]) => [event.payload, ...prevLogs].slice(0, 100)); // Keep last 100 logs
      shouldScrollRef.current = true;
    });

    return () => {
      unlisten.then((f: () => void) => f());
    };
  }, []);

  useEffect(() => {
    if (shouldScrollRef.current && scrollRef.current) {
      scrollRef.current.scrollTop = 0;
      shouldScrollRef.current = false;
    }
  });

  return (
    <div className="p-4 h-full flex flex-col space-y-4">
      <Card className="h-full flex flex-col">
        <CardHeader className="flex-shrink-0 flex flex-row items-center justify-between">
          <CardTitle>Real-time Webhook Logs</CardTitle>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setLogs([])}
            disabled={logs.length === 0}
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Clear Logs
          </Button>
        </CardHeader>
        <CardContent
          ref={scrollRef}
          className="flex-grow min-h-0 overflow-y-auto space-y-3 pr-2"
        >
          {logs.length === 0 ? (
            <div className="text-center text-muted-foreground pt-12">
              Listening for webhook events...
            </div>
          ) : (
            logs.map((log: WebhookLog, index: number) => (
              <div
                key={`${log.timestamp}-${index}`}
                className={`flex items-start gap-3 p-2 rounded-md ${log.success ? "bg-green-100 dark:bg-green-900/30" : "bg-red-100 dark:bg-red-900/30"}`}
              >
                {log.success ? (
                  <CheckCircle2 className="w-5 h-5 mt-1 flex-shrink-0" />
                ) : (
                  <XCircle className="w-5 h-5 mt-1 flex-shrink-0" />
                )}
                <div className="flex-grow">
                  <p className="font-mono text-xs opacity-80">
                    {new Date(log.timestamp).toLocaleString()}
                  </p>
                  <p className="font-semibold">{log.details}</p>
                  {log.error_message && (
                    <p className="text-xs opacity-90">{log.error_message}</p>
                  )}
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
