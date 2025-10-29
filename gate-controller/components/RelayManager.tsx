'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RelaySettingsTab } from './RelaySettingsTab';
import { WebhookLogsTab } from './WebhookLogsTab';
import { RelayListTab } from './RelayListTab';
import { SlidersHorizontal, List, Bot } from 'lucide-react';

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
