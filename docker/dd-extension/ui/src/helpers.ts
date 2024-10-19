import { v1 } from '@docker/extension-api-client-types';

export function openBrowserUrl(ddClient: v1.DockerDesktopClient, url:string){
    ddClient.host.openExternal(url);
}

