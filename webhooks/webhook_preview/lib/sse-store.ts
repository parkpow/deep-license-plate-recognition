import { WebhookData } from "@/types/webhook";

type Client = {
  id: string;
  res: Response;
};

const clients: Map<string, Client[]> = new Map();

export function addClient(uuid: string, client: Client) {
  const current = clients.get(uuid) || [];
  clients.set(uuid, [...current, client]);
}

export function removeClient(uuid: string, clientId: string) {
  const current = clients.get(uuid) || [];
  clients.set(
    uuid,
    current.filter((c) => c.id !== clientId),
  );
}

export function sendEvent(uuid: string, data: WebhookData) {
  const current = clients.get(uuid) || [];
  current.forEach((client) => {
    try {
      client.res.write?.(`data: ${JSON.stringify(data)}\n\n`);
    } catch (err) {
      console.error("Erro ao enviar SSE:", err);
    }
  });
}
