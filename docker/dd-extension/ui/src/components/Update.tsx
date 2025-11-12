import { useState } from "react";
import { Button, Row } from "react-bootstrap";
import Form from "react-bootstrap/Form";
import { useDockerDesktopClient } from "../hooks/useDockerDesktopClient";

import Loader from "./Loader";

interface UpdateProps {
  isEnabled: boolean;
  image: string;
}
export default function Update({ isEnabled, image }: UpdateProps) {
  const [isLoading, setLoading] = useState(false);
  const ddClient = useDockerDesktopClient();

  if (!isEnabled) return null;

  const handleUpdateImage = () => {
    setLoading(true);
    ddClient.docker.cli
      .exec("pull", [image])
      .then((result) => {
        console.debug(result);
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
          id="update-image-btn"
          disabled={isLoading}
        >
          <Loader isLoading={isLoading} />
          Update
        </Button>
      </div>
      <label
        className="col-auto align-self-center form-label"
        htmlFor="update-image-btn"
      >
        Update the Docker image.
      </label>
    </Form.Group>
  );
}
