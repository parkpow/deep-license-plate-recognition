"use client";

import { invoke } from "@tauri-apps/api/core";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useState } from "react";
import { toast } from "sonner";
import {
  HardDrive,
  Usb,
  Trash2,
  ClipboardCopy,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { ApiInstructionsModal } from "@/components/ApiInstructionsModal";

interface ConfiguredRelay {
  id: string;
  type: "ch340" | "hw348" | "cp210x";
  channels?: number;
}

interface ConfiguredRelayCardProps {
  relay: ConfiguredRelay;
  onRelayRemoved: () => void;
}

export function ConfiguredRelayCard({
  relay,
  onRelayRemoved,
}: ConfiguredRelayCardProps) {
  const [showApiInstructions, setShowApiInstructions] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleAction = async (
    action: "on" | "off",
    channel: number | null = null,
  ) => {
    try {
      await invoke("trigger_relay_action", {
        payload: { id: relay.id, action, channel },
      });
      toast.success(
        `Action '${action}' sent to ${relay.id}${
          channel ? ` on channel ${channel}` : ""
        }`,
      );
    } catch (error) {
      toast.error(`Failed to trigger ${relay.id}`, {
        description: String(error),
      });
    }
  };

  const handleRemove = async () => {
    try {
      await invoke("remove_relay", { id: relay.id });
      toast.success("Relay Removed", {
        description: `${relay.id} has been removed from configuration.`,
      });
      onRelayRemoved();
    } catch (error) {
      toast.error("Failed to remove relay", { description: String(error) });
    }
  };

  const isSerial = relay.type === "ch340" || relay.type === "cp210x";

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className="flex-shrink-0">
              {isSerial ? (
                <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                  <HardDrive className="w-4 h-4 text-primary" />
                </div>
              ) : (
                <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                  <Usb className="w-4 h-4 text-primary" />
                </div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold truncate">{relay.id}</h3>
              <p className="text-xs text-muted-foreground">
                {relay.type === "ch340" && `CH340`}
                {relay.type === "hw348" && `HW-348`}
                {relay.type === "cp210x" && `CP210x`}
                {relay.channels && ` • ${relay.channels}ch`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            {relay.channels && relay.channels > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={() => setShowApiInstructions(true)}
            >
              <ClipboardCopy className="w-4 h-4" />
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently remove the relay{" "}
                    <strong>{relay.id}</strong> from your configuration.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleRemove}>
                    Continue
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardHeader>

      {isExpanded &&
        relay.channels &&
        relay.channels > 0 && (
          <CardContent className="p-3 pt-0">
            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
              {[...Array(relay.channels)].map((_, i) => {
                const channel = i + 1;
                return (
                  <div key={channel} className="flex flex-col gap-1">
                    <span className="text-xs font-mono text-center text-muted-foreground">
                      Ch {channel}
                    </span>
                    <Button
                      size="sm"
                      className="bg-green-600 hover:bg-green-700 text-xs h-7 px-2"
                      onClick={() => handleAction("on", channel)}
                    >
                      ON
                    </Button>
                    <Button
                      size="sm"
                      className="bg-red-600 hover:bg-red-700 text-xs h-7 px-2"
                      onClick={() => handleAction("off", channel)}
                    >
                      OFF
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        )}

      <ApiInstructionsModal
        relay={relay}
        isOpen={showApiInstructions}
        onClose={() => setShowApiInstructions(false)}
      />
    </Card>
  );
}
