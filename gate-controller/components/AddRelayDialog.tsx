"use client";

import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface UsbRelayInfo {
  serial_number: string;
  relay_type: string;
}

interface AddRelayDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onRelayAdded: () => void;
}

const getChannelCount = (relayType: string | undefined): number => {
  if (!relayType) return 0;
  const digitMatch = relayType.match(/(\d+)Channel/);
  if (digitMatch) return parseInt(digitMatch[1], 10);
  const wordMap: { [key: string]: number } = {
    One: 1,
    Two: 2,
    Four: 4,
    Eight: 8,
  };
  for (const word in wordMap) {
    if (relayType.startsWith(word)) return wordMap[word];
  }
  return 0;
};

export function AddRelayDialog({
  open,
  onOpenChange,
  onRelayAdded,
}: AddRelayDialogProps) {
  const [availablePorts, setAvailablePorts] = useState<string[]>([]);
  const [selectedPort, setSelectedPort] = useState<string>("");

  const [availableUsbRelays, setAvailableUsbRelays] = useState<UsbRelayInfo[]>([]);
  const [selectedUsbRelay, setSelectedUsbRelay] = useState<UsbRelayInfo | null>(null);

  const [ch340Channels, setCh340Channels] = useState(1);
  const [cp210xChannels, setCp210xChannels] = useState(1);

  const refreshSerialPorts = async () => {
    try {
      const ports = await invoke<string[]>("list_serial_ports");
      setAvailablePorts(ports);
      if (ports.length > 0) setSelectedPort(ports[0]);
    } catch (error) {
      toast.error("Failed to list serial ports", {
        description: String(error),
      });
    }
  };

  const refreshUsbRelays = async () => {
    try {
      const relays = await invoke<UsbRelayInfo[]>("list_hw348_relays");
      setAvailableUsbRelays(relays);
      if (relays.length > 0) setSelectedUsbRelay(relays[0]);
    } catch (error) {
      toast.error("Failed to list HW-348 relays", { description: String(error) });
    }
  };

  useEffect(() => {
    if (open) {
      refreshSerialPorts();
      refreshUsbRelays();
    }
  }, [open]);

  const handleAddCh340 = async () => {
    if (!selectedPort) {
      toast.warning("Please select a serial port.");
      return;
    }
    if (ch340Channels <= 0) {
      toast.warning("Number of channels must be greater than 0.");
      return;
    }
    try {
      await invoke("add_ch340_relay", { port: selectedPort, channels: ch340Channels });
      toast.success("CH340 Relay Added", {
        description: `Port ${selectedPort} has been configured with ${ch340Channels} channels.`,
      });
      onRelayAdded();
      onOpenChange(false);
    } catch (error) {
      toast.error("Failed to add CH340 relay", { description: String(error) });
    }
  };

  const handleAddHw348 = async () => {
    if (!selectedUsbRelay) {
      toast.warning("Please select a USB relay.");
      return;
    }
    try {
      const channels = getChannelCount(selectedUsbRelay.relay_type);
      await invoke("add_hw348_relay", {
        serialNumber: selectedUsbRelay.serial_number,
        channels,
      });
      toast.success("HW-348 Relay Added", {
        description: `Relay ${selectedUsbRelay.serial_number} has been configured.`,
      });
      onRelayAdded();
      onOpenChange(false);
    } catch (error) {
      toast.error("Failed to add HW-348 relay", { description: String(error) });
    }
  };

  const handleAddCp210x = async () => {
    if (!selectedPort) {
      toast.warning("Please select a serial port.");
      return;
    }
    if (cp210xChannels <= 0) {
      toast.warning("Number of channels must be greater than 0.");
      return;
    }
    try {
      await invoke("add_cp210x_relay", {
        port: selectedPort,
        channels: cp210xChannels,
      });
      toast.success("CP210x Relay Added", {
        description: `Port ${selectedPort} has been configured with ${cp210xChannels} channels.`,
      });
      onRelayAdded();
      onOpenChange(false);
    } catch (error) {
      toast.error("Failed to add CP210x relay", { description: String(error) });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add a New Relay</DialogTitle>
          <DialogDescription>
            Choose the chip of your USB relay you want to configure.
          </DialogDescription>
        </DialogHeader>
        <Tabs defaultValue="ch340" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="ch340">CH340</TabsTrigger>
            <TabsTrigger value="hw348">HW-348</TabsTrigger>
            <TabsTrigger value="cp210x">CP210x</TabsTrigger>
          </TabsList>
          <TabsContent value="ch340">
            <div className="space-y-4 py-4">
              <div className="flex items-center gap-4">
                <Select value={selectedPort} onValueChange={setSelectedPort}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a serial port..." />
                  </SelectTrigger>
                  <SelectContent>
                    {availablePorts.map((port) => (
                      <SelectItem key={port} value={port}>
                        {port}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="outline" onClick={refreshSerialPorts}>
                  Refresh
                </Button>
              </div>
              <div className="flex items-center gap-4">
                <label htmlFor="channels-ch340" className="text-sm font-medium">
                  Channels
                </label>
                <Input
                  id="channels-ch340"
                  type="number"
                  value={ch340Channels}
                  onChange={(e) => setCh340Channels(parseInt(e.target.value, 10) || 1)}
                  className="w-full"
                  min={1}
                />
              </div>
              <Button
                className="w-full"
                onClick={handleAddCh340}
                disabled={!selectedPort}
              >
                Add Relay
              </Button>
            </div>
          </TabsContent>
          <TabsContent value="hw348">
            <div className="space-y-4 py-4">
              <div className="flex items-center gap-4">
                <Select
                  value={selectedUsbRelay?.serial_number || ""}
                  onValueChange={(sn) =>
                    setSelectedUsbRelay(
                      availableUsbRelays.find((r) => r.serial_number === sn) || null,
                    )
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a USB relay..." />
                  </SelectTrigger>
                  <SelectContent>
                    {availableUsbRelays.map((r) => (
                      <SelectItem key={r.serial_number} value={r.serial_number}>
                        {r.serial_number} ({r.relay_type})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="outline" onClick={refreshUsbRelays}>
                  Refresh
                </Button>
              </div>
              <Button
                className="w-full"
                onClick={handleAddHw348}
                disabled={!selectedUsbRelay}
              >
                Add Relay
              </Button>
            </div>
          </TabsContent>
          <TabsContent value="cp210x">
            <div className="space-y-4 py-4">
              <div className="flex items-center gap-4">
                <Select value={selectedPort} onValueChange={setSelectedPort}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a serial port..." />
                  </SelectTrigger>
                  <SelectContent>
                    {availablePorts.map((port) => (
                      <SelectItem key={port} value={port}>
                        {port}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="outline" onClick={refreshSerialPorts}>
                  Refresh
                </Button>
              </div>
              <div className="flex items-center gap-4">
                <label htmlFor="channels" className="text-sm font-medium">
                  Channels
                </label>
                <Input
                  id="channels"
                  type="number"
                  value={cp210xChannels}
                  onChange={(e) => setCp210xChannels(parseInt(e.target.value, 10) || 1)}
                  className="w-full"
                  min={1}
                />
              </div>
              <Button
                className="w-full"
                onClick={handleAddCp210x}
                disabled={!selectedPort}
              >
                Add Relay
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
