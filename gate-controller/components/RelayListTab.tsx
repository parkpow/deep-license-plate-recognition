"use client";

import { invoke } from "@tauri-apps/api/core";
import { PlusCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { AddRelayDialog } from "@/components/AddRelayDialog";
import { ConfiguredRelayCard } from "@/components/ConfiguredRelayCard";
import { Button } from "@/components/ui/button";

interface ConfiguredRelay {
  id: string;
  type: "ch340" | "hw348" | "cp210x";
  channels?: number;
}

export function RelayListTab() {
  const [relays, setRelays] = useState<ConfiguredRelay[]>([]);
  const [isAddDialogOpen, setAddDialogOpen] = useState(false);

  const fetchConfiguredRelays = async () => {
    try {
      const configuredRelays = await invoke<ConfiguredRelay[]>("get_configured_relays");
      setRelays(configuredRelays);
    } catch (error) {
      toast.error("Failed to load relay configuration", { description: String(error) });
    }
  };

  useEffect(() => {
    fetchConfiguredRelays();
  }, []);

  return (
    <div className="w-full h-full flex flex-col space-y-4">
      <div className="flex items-center justify-between flex-shrink-0">
        <h2 className="text-2xl font-bold">Configured Relays</h2>
        <Button onClick={() => setAddDialogOpen(true)}>
          <PlusCircle className="w-4 h-4 mr-2" />
          Add Relay
        </Button>
      </div>

      <div className="flex-grow min-h-0">
        {relays.length > 0 ? (
          <div className="h-full overflow-y-auto pr-2">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {relays.map((relay) => (
                <ConfiguredRelayCard
                  key={relay.id}
                  relay={relay}
                  onRelayRemoved={fetchConfiguredRelays}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center h-full flex flex-col justify-center items-center py-12 px-6 border-2 border-dashed rounded-lg">
            <h3 className="text-lg font-semibold text-muted-foreground">
              No Relays Configured
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              Click &quot;Add Relay&quot; to get started.
            </p>
          </div>
        )}
      </div>

      <AddRelayDialog
        open={isAddDialogOpen}
        onOpenChange={setAddDialogOpen}
        onRelayAdded={fetchConfiguredRelays}
      />
    </div>
  );
}
