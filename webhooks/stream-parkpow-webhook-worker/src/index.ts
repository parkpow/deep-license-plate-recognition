/**
 * Secure middleware to forward Stream webhook results to ParkPow
 * Adds authentication token from environment secrets
 */

interface Env {
  PARKPOW_ENDPOINT: string;
  PARKPOW_TOKEN: string;
}

export default {
  async fetch(request, env, ctx): Promise<Response> {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    try {
      const payload = await request.json();

      const parkpowRequest = new Request(env.PARKPOW_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${env.PARKPOW_TOKEN}`,
        },
        body: JSON.stringify(payload),
      });

      const response = await fetch(parkpowRequest);

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
      });
    } catch (error) {
      console.error("Error forwarding webhook:", error);
      return new Response("Internal server error", { status: 500 });
    }
  },
} satisfies ExportedHandler<Env>;
