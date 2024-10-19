import { createDockerDesktopClient } from "@docker/extension-api-client";
// Note: This line relies on Docker Desktop's presence as a host application.
// If you're running this React app in a browser, it won't work properly.
const client = createDockerDesktopClient();

export function useDockerDesktopClient() {
  return client;
}