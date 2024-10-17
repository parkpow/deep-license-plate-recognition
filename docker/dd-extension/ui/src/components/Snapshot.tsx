import {
  Container,
  Row,
  Col,
  Card,
  Button,
  Alert,
  Navbar,
  Nav,
} from "react-bootstrap";

import Form from "react-bootstrap/Form";

// import { verifyToken } from "./helpers";
import React, { useState } from "react";
import { useDockerDesktopClient } from "../hooks/useDockerDesktopClient";
import Loader from "./Loader";
import Uninstall from "./Uninstall";
import Update from "./Update";
import ShowCommand from "./ShowCommand";
import {openBrowserUrl} from '../helpers'


const snapshotImageOptions = [
  {
    label: "Intel CPU",
    value: "platerecognizer/alpr:latest",
    uninstall: true,
  },
  {
    label: "Raspberry",
    value: "platerecognizer/alpr-raspberry-pi:latest",
    uninstall: false,
  },
  {
    label: "GPU (Nvidia Only)",
    value: "platerecognizer/alpr-gpu:latest",
    uninstall: false,
  },
  {
    label: "Jetson Nano",
    value: "platerecognizer/alpr-jetson:latest",
    uninstall: true,
  },
  {
    label: "ZCU104",
    value: "platerecognizer/alpr-zcu104:latest",
    uninstall: false,
  },
  {
    label: "Thailand",
    value: "platerecognizer/alpr:thailand",
    uninstall: false,
  },
];

const DEFAULT_SNAPSHOT_IMAGE = snapshotImageOptions[0]["value"];

export default function Snapshot() {
  const [tokenValidated, setTokenValidated] = useState(false);
  const [uninstall, setUninstall] = useState(true);
  const [isLoading, setLoading] = useState(false);
  const [command, setCommand] = useState<string>("");
  const [curlPort, setCurlPort] = useState("");
  const [image, setImage] = useState(DEFAULT_SNAPSHOT_IMAGE);
  const ddClient = useDockerDesktopClient();

  const handleInputChange = (e: any) => {
    setTokenValidated(false);
  };

  const handleImageChange = (e: any) => {
    setTokenValidated(false);
    let image: string = e.target.value;
    setImage(image);
    const snapshotImageOption: any = snapshotImageOptions.find((element) => {
      return element.value === image;
    });
    setUninstall(snapshotImageOption.uninstall);
  };

  interface SnapshotData {
    port: string;
    license: string;
    token: string;
    image: string;
  }

  const handleSubmit = async (event: React.SyntheticEvent) => {
    event.preventDefault();
    const form: any = event.target;
    const formData = new FormData(form);

    const data: any = Object.fromEntries(formData.entries());
    // console.log(data);
    setCurlPort(data.port);
    setLoading(true);

    ddClient.extension.vm?.service
      ?.post("/verify-token", data)
      .then((res: any) => {
        console.debug(res);
        const valid = res["valid"];
        const message = res["message"];
        if (valid) {
          // Pull image and update
          ddClient.docker.cli.exec("pull", [data.image]).then((result) => {
            const autoBoot = data.startOnBoot
              ? " --restart unless-stopped"
              : "--rm";
            const gpus = data.image.includes("gpu") ? " --gpus all" : "";
            const nvidia = data.image.includes("jetson")
              ? " --runtime nvidia"
              : "";
            const command = `docker run${gpus}${nvidia}${autoBoot} -t -p ${data.port}:8080 -v license:/license -e LICENSE_KEY=${data.license} -e TOKEN=${data.token} ${data.image}`;
            setCommand(command);
            setTokenValidated(valid);
            setLoading(false);
          });
        } else {
          setLoading(false);
          ddClient.desktopUI.toast.error(`Verify Token: ${message}`);
        }
      });
  };

  const handleLinkClick = (e: any) => {
    e.preventDefault();
    openBrowserUrl(ddClient, e.target.href);
  };
  return (
    <Form onSubmit={handleSubmit}>
      <Loader isLoading={isLoading} />

      <Form.Group as={Row} className="mb-3" controlId="snapshotToken">
        <Form.Label column sm={4}>
          Please enter your Plate Recognizer{" "}
          <a href="https://app.platerecognizer.com/service/snapshot-sdk/" onClick={handleLinkClick}>
            API Token
          </a>
          :
        </Form.Label>
        <Col sm={8}>
          <Form.Control
            type="text"
            placeholder="Token"
            required
            name="token"
            onChange={handleInputChange}
          />
        </Col>
      </Form.Group>

      <Form.Group as={Row} className="mb-3" controlId="snapshotLicense">
        <Form.Label column sm={4}>
          Please enter your{" "}
          <a href="https://app.platerecognizer.com/accounts/plan/#sdk/?utm_source=dd-extension&utm_medium=app" onClick={handleLinkClick}>
            Snapshot License Key
          </a>
          :
        </Form.Label>
        <Col sm={8}>
          <Form.Control
            type="text"
            placeholder="License Key"
            required
            name="license"
            onChange={handleInputChange}
          />
        </Col>
      </Form.Group>

      <Form.Group as={Row} className="mb-3" controlId="snapshotRestartPolicy">
        <Form.Label column sm={4}>
          Start Snapshot automatically on system startup?
        </Form.Label>
        <Col sm={8} className="mt-2">
          <Form.Check
            type="switch"
            name="startOnBoot"
            onChange={handleInputChange}
          />
        </Col>
      </Form.Group>

      <Form.Group as={Row} className="mb-3" controlId="snapshotPort">
        <Form.Label column sm={4}>
          Set the container port (default is 8080):
        </Form.Label>
        <Col sm={8}>
          <Form.Control
            type="number"
            min="0"
            max="65535"
            placeholder="Port"
            name="port"
            required
            defaultValue={8080}
            onChange={handleInputChange}
          />
        </Col>
      </Form.Group>

      <Form.Group as={Row} className="mb-3" controlId="snapshotDockerImage">
        <Form.Label column sm={4}>
          Docker image to use:
        </Form.Label>
        <Col sm={8}>
          <Form.Select
            aria-label="Snapshot Docker Image"
            onChange={handleImageChange}
            name="image"
            defaultValue={image}
          >
            {snapshotImageOptions.map((snapshotImageOption, index) => (
              <option value={snapshotImageOption.value} key={index}>
                {snapshotImageOption.label}
              </option>
            ))}
          </Form.Select>
        </Col>
      </Form.Group>

      <ShowCommand
        curlPort={curlPort}
        command={command}
        validated={tokenValidated}
      />

      <Form.Group as={Row} className="mb-3">
        <div className="col-2">
          <Button className="btn btn-primary" type="submit">
            Show Docker Command
          </Button>
        </div>
        <label className="col-auto align-self-center form-label">
          Confirm settings and show docker command.
        </label>
      </Form.Group>

      <Update isEnabled={uninstall} image={image} />
      <Uninstall isEnabled={uninstall} image={image} />
    </Form>
  );
}
