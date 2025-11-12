'use client';

import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Copy, Eye, EyeOff, RefreshCw } from 'lucide-react';

export function RelaySettingsTab() {
  const [token, setToken] = useState<string | null>(null);
  const [showToken, setShowToken] = useState(false);

  const fetchToken = async () => {
    try {
      const currentToken = await invoke<string | null>('get_webhook_token');
      setToken(currentToken);
    } catch (error) {
      toast.error('Failed to load webhook token', { description: String(error) });
    }
  };

  const regenerateToken = async () => {
    try {
      const newToken = await invoke<string>('regenerate_webhook_token');
      setToken(newToken);
      toast.success('New webhook token generated!');
    } catch (error) {
      toast.error('Failed to generate new token', { description: String(error) });
    }
  };

  const copyToClipboard = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      toast.success('Token copied to clipboard!');
    }
  };

  useEffect(() => {
    fetchToken();
  }, []);

  return (
    <div className="p-4 space-y-6 h-full overflow-y-auto">
      <Card>
        <CardHeader>
          <CardTitle>Webhook Security <span className="text-red-500">*</span></CardTitle>
          <CardDescription>
            Protect your webhook endpoint with a secret token. This is mandatory for all API requests. Include this token in the `Authorization` header of your requests as a Bearer token.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Input
              type={showToken ? 'text' : 'password'}
              readOnly
              value={token || 'No token generated yet'}
              className="font-mono"
            />
            <Button variant="outline" size="icon" onClick={() => setShowToken(!showToken)} disabled={!token}>
              {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </Button>
            <Button variant="outline" size="icon" onClick={copyToClipboard} disabled={!token}>
              <Copy className="w-4 h-4" />
            </Button>
          </div>
          <Button onClick={regenerateToken}>
            <RefreshCw className="w-4 h-4 mr-2" />
            {token ? 'Regenerate Token' : 'Generate Token'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
            <CardTitle>API Usage Example</CardTitle>
            <CardDescription>Example of how to trigger a relay using `curl`.</CardDescription>
        </CardHeader>
        <CardContent className='font-mono text-sm bg-muted p-4 rounded-lg'>
            <pre><code>
{`curl -X POST http://localhost:4848/webhook \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${token || '<YOUR_TOKEN>'}" \
  -d '{ "id": "<YOUR_RELAY_ID>", "action": "on", "channel": 1 }'`}
            </code></pre>
        </CardContent>
      </Card>
    </div>
  );
}
