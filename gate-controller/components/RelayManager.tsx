"use client";

import { Bot, List, SlidersHorizontal } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RelayListTab } from "./RelayListTab";
import { RelaySettingsTab } from "./RelaySettingsTab";
import { WebhookLogsTab } from "./WebhookLogsTab";

export default function RelayManager() {
  return (
    <div className="w-full h-full flex flex-col">
      <Tabs defaultValue="relays" className="w-full h-full flex flex-col">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="relays">
            <List className="w-4 h-4 mr-2" />
            Relays
          </TabsTrigger>
          <TabsTrigger value="settings">
            <SlidersHorizontal className="w-4 h-4 mr-2" />
            Settings
          </TabsTrigger>
          <TabsTrigger value="logs">
            <Bot className="w-4 h-4 mr-2" />
            Webhook Logs
          </TabsTrigger>
        </TabsList>
        <TabsContent value="relays" className="flex-grow min-h-0">
          <RelayListTab />
        </TabsContent>
        <TabsContent value="settings" className="flex-grow min-h-0">
          <RelaySettingsTab />
        </TabsContent>
        <TabsContent value="logs" className="flex-grow min-h-0">
          <WebhookLogsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
