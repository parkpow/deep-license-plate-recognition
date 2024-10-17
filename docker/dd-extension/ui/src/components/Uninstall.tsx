import React, { useState } from "react";
import { useDockerDesktopClient } from "../hooks/useDockerDesktopClient";
import Form from "react-bootstrap/Form";
import {
  Row,
  Button,
} from "react-bootstrap";

import Loader from "./Loader";
interface UninstallProps {
  isEnabled: boolean;
  image: string;
}
export default function Uninstall({ isEnabled, image }: UninstallProps) {
  if (!isEnabled) {
    return null;
  }
  const [isLoading, setLoading] = useState(false);
  const ddClient = useDockerDesktopClient();

  const handleUninstall = (e: any) => {
    setLoading(true);
    ddClient.docker.cli
      .exec("ps", [
        "--all",
        "--format",
        '"{{json .}}"',
        "--filter",
        `ancestor=${image}`,
      ])
      .then(async (result) => {
        // result.parseJsonLines() parses the output of the command into an array of objects
        const containers = result.parseJsonLines();
        for (let index = 0; index < containers.length; index++) {
          const container = containers[index];
          await ddClient.docker.cli.exec("container", ["rm", container.ID]);
        }
        const rmiResult = await ddClient.docker.cli.exec("rmi", [image, "-f"]);
        console.debug(rmiResult);
        await ddClient.docker.cli.exec("image", ["prune", "-f"]);
        setLoading(false);
      })
      .catch((err) => {
        ddClient.desktopUI.toast.error(`Uninstall Snapshot Error`);
        console.error(err);
        setLoading(false);
      });
  };

  return (
    <Form.Group as={Row} className="mb-3">
      <div className="col-2">
        <Button
          className="btn btn-danger"
          type="button"
          onClick={handleUninstall}
        >
          <Loader isLoading={isLoading} />
          Uninstall
        </Button>
      </div>
      <label className="col-auto align-self-center form-label">
        Remove the Docker image and mark the product as uninstalled.
      </label>
    </Form.Group>
  );
}
