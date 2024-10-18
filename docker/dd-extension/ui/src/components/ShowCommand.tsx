import React, { useState } from "react";
import { useDockerDesktopClient } from "../hooks/useDockerDesktopClient";
import Form from "react-bootstrap/Form";
import {
  Row,
} from "react-bootstrap";
import Loader from "./Loader";

interface ShowCommandProps {
  validated: boolean;
  command: string;
  curlPort: string;
}

export default function ShowCommand({
  validated,
  command,
  curlPort,
}: ShowCommandProps) {
  const [isRunningCommand, setRunningCommand] = useState(false);

  if (!validated) {
    return null;
  }
  const ddClient = useDockerDesktopClient();

  function copyToClipboard(e: any) {
    navigator.clipboard
      .writeText(command)
      .then(() => {
        ddClient.desktopUI.toast.success("Text copied to clipboard!");
      })
      .catch((err) => {
        ddClient.desktopUI.toast.error(`Failed to copy text: ${err}`);
      });
  }

  function runCommand(e: any){
    setRunningCommand(true);
    // Generate list of run options
    console.debug(command);
    const cmd:any = command.match(/[^ ]+/g)?.slice(2);
    // Run in the background
    if (!cmd.includes('-d')){
      cmd.unshift('-d')
    }

    ddClient.docker.cli.exec("run", cmd).then(async (result) => {
      console.debug(result);
      setRunningCommand(false);
      ddClient.desktopUI.toast.success('Command Ran Successfully.');
      await ddClient.desktopUI.navigate.viewContainer(result.stdout.trim())
    }).catch(e => {
      setRunningCommand(false);
      console.error(e);
      ddClient.desktopUI.toast.error('Failed Run Command.');
    })
  }

  const curlCommand = curlPort ? (
    <div>
      <p className="card-title mt-3 mb-0" style={{ display: "inline-block" }}>
        To use the SDK endpoint call:{" "}
      </p>
      <code>
        {" "}
        curl -F "upload=@my_file.jpg" http://localhost:{curlPort}
        /v1/plate-reader/
      </code>
    </div>
  ) : null;

  return (
    <Form.Group as={Row} className="mb-3">
      <div style={{ display: "block" }}>
        <div className="mt-3 card" style={{ display: "block" }}>
          <div className="card-body">
            <p className="card-title">
              You can now start {curlPort ? 'Snapshot' : 'Stream'}. Open a terminal and type the command
              below. You can save this command for future use.
            </p>
            <code className="card-text d-block">{command}</code>
            <div className="mt-3">
              <button
                className="btn btn-sm btn-success mx-2"
                style={{ borderRadius: 15 }}
                type="button"
                onClick={runCommand}
              >
                <Loader isLoading={isRunningCommand} /> Run
              </button>
              <button
                className="btn btn-sm btn-warning mx-2"
                style={{ borderRadius: 15 }}
                type="button"
                onClick={copyToClipboard}
              >
                copy to clipboard
              </button>
              <span className="ms-2" style={{ fontSize: 13, color: "green" }} />
            </div>
            {curlCommand}
          </div>
        </div>
      </div>
    </Form.Group>
  );
}
