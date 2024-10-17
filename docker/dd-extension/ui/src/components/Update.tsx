import React, { useState } from "react";
import { useDockerDesktopClient } from "../hooks/useDockerDesktopClient";
import Form from "react-bootstrap/Form";
import {

  Row,

  Button,

} from "react-bootstrap";

import Loader from "./Loader";

interface UpdateProps {
  isEnabled: boolean;
  image: string;
}
export default function Update({ isEnabled, image }: UpdateProps) {
  if (!isEnabled) {
    return null;
  }
  const [isLoading, setLoading] = useState(false);
  const ddClient = useDockerDesktopClient();

  const handleUpdateImage = (e: any) => {
    setLoading(true);
    ddClient.docker.cli
      .exec("pull", [image])
      .then((result) => {
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        ddClient.desktopUI.toast.error(`Update Snapshot: ${err.message}`);
        setLoading(false);
      });
  };

  return (
    <Form.Group as={Row} className="mb-3 {'d-none': uninstall }">
      <div className="col-2">
        <Button
          className="btn btn-secondary"
          type="button"
          onClick={handleUpdateImage}
        >
          <Loader isLoading={isLoading} />
          Update
        </Button>
      </div>
      <label className="col-auto align-self-center form-label">
        Update the Docker image.
      </label>
    </Form.Group>
  );
}
