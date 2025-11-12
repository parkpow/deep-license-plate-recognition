'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { ClipboardCopy } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';

interface Relay {
  id: string;
  type: 'ch340' | 'hw348' | 'cp210x';
  channels?: number;
}

interface ApiInstructionsModalProps {
  relay: Relay;
  isOpen: boolean;
  onClose: () => void;
}

const CodeBlock = ({ payload }: { payload: object }) => {
    const payloadString = JSON.stringify(payload, null, 2);

    const handleCopy = () => {
        navigator.clipboard.writeText(payloadString);
        toast.success('Payload copied to clipboard!');
    };

    return (
        <div className="relative bg-gray-900 text-white rounded-md p-4 font-mono text-sm my-2">
            <Button variant="ghost" size="icon" className="absolute top-2 right-2 h-8 w-8" onClick={handleCopy}>
                <ClipboardCopy className="h-4 w-4" />
            </Button>
            <pre><code>{payloadString}</code></pre>
        </div>
    );
};

export function ApiInstructionsModal({ relay, isOpen, onClose }: ApiInstructionsModalProps) {
    const [webhookUrl, setWebhookUrl] = useState('');
    const isMultiChannel = relay.type === 'ch340' || relay.type === 'hw348' || relay.type === 'cp210x';

    useEffect(() => {
        async function getToken() {
            try {
                const token = await invoke('get_webhook_token');
                // Assuming the server runs on localhost:4848
                // This could be made configurable in the future
                setWebhookUrl(`http://localhost:4848/webhook/${token}`);
            } catch (error) {
                console.error("Failed to get webhook token:", error);
                setWebhookUrl('Could not retrieve webhook URL.');
            }
        }
        if (isOpen) {
            getToken();
        }
    }, [isOpen]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-lg">API Instructions for {relay.id}</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
            <div className="md:col-span-2">
                <h3 className="font-semibold text-sm">Payloads</h3>
                <p className="text-xs text-gray-500 mb-1">The body of your POST request must be a JSON object with one of the following structures.</p>

                <h4 className="font-medium text-sm">Standard Actions</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
                    <CodeBlock payload={{ id: relay.id, action: 'on', ...(isMultiChannel && { channel: 1 }) }} />
                    <CodeBlock payload={{ id: relay.id, action: 'off', ...(isMultiChannel && { channel: 1 }) }} />
                </div>

                <h4 className="font-medium text-sm mt-2">Toggle Actions</h4>
                <p className="text-xs text-gray-500 mb-1">
                    The <code>toggle</code> parameter inverts the action after a <code>period</code> (in milliseconds).
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
                    <CodeBlock payload={{ id: relay.id, action: 'on', toggle: true, period: 5000, ...(isMultiChannel && { channel: 1 }) }} />
                    <CodeBlock payload={{ id: relay.id, action: 'off', toggle: true, period: 5000, ...(isMultiChannel && { channel: 1 }) }} />
                </div>

                {isMultiChannel && relay.channels && relay.channels > 1 && (
                    <p className="text-xs text-gray-500 mt-1">For this relay, you can change the <code>channel</code> value from 1 to {relay.channels}.</p>
                )}
            </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
