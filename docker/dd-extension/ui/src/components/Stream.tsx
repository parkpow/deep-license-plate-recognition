import {
  Row,
  Col,
  Button,
} from "react-bootstrap";
import React, { useState } from "react";

import { useDockerDesktopClient } from "../hooks/useDockerDesktopClient";

import Form from "react-bootstrap/Form";
import Uninstall from "./Uninstall";
import Update from "./Update";

import { openBrowserUrl } from "../helpers";
import ShowCommand from "./ShowCommand";
import Loader from "./Loader";

export default function Stream() {
  const STREAM_IMAGE = "platerecognizer/alpr-stream";
  const [command, setCommand] = useState<string>("");
  const [license, setLicense] = useState<string>("");
  const [tokenValidated, setTokenValidated] = useState(false);
  const [isLoading, setLoading] = useState(false);

  const ddClient = useDockerDesktopClient();

  const handleLinkClick = (e: any) => {
    e.preventDefault();
    openBrowserUrl(ddClient, e.target.href);
  };

  const handleConfigureClick = (e: any) => {
    if (license) {
      const url = "https://app.platerecognizer.com/stream-config/" + license;
      openBrowserUrl(ddClient, url);
    } else {
      ddClient.desktopUI.toast.error("License Key is required");
    }
  };
  const handleInputChange = (e: any) => {
    const { name, value } = e.target;
    if (name == "license") {
      setLicense(value);
    }
    setTokenValidated(false);
  };

  const handleSubmit = async (event: React.SyntheticEvent) => {
    event.preventDefault();
    const form: any = event.target;
    const formData = new FormData(form);

    const data: any = Object.fromEntries(formData.entries());
    // console.log(data);
    setLoading(true);
    ddClient.extension.vm?.service
      ?.post("/verify-token", data)
      .then((res: any) => {
        console.debug(res);
        const valid = res["valid"];
        const message = res["message"];
        if (valid) {
          // Pull image and update
          ddClient.docker.cli.exec("pull", [STREAM_IMAGE]).then((result) => {
            const autoBoot = data['restart-policy'] != 'no'
              ? " --restart "+data['restart-policy']
              : "--rm";
            const command = `docker run ${autoBoot} -t -v ${data.streamPath}:/user-data/ -e LICENSE_KEY=${data.license} -e TOKEN=${data.token} ${STREAM_IMAGE}`;
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

  return (
    <Form onSubmit={handleSubmit}>
      <Loader isLoading={isLoading} />
      <Form.Group as={Row} className="mb-3" controlId="streamToken">
        <Form.Label column sm={4}>
          Please enter your Plate Recognizer{" "}
          <a
            href="https://app.platerecognizer.com/service/stream/"
            onClick={handleLinkClick}
          >
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

      <Form.Group as={Row} className="mb-3" controlId="streamLicense">
        <Form.Label column sm={4}>
          Please enter your{" "}
          <a
            href="https://app.platerecognizer.com/service/stream/"
            onClick={handleLinkClick}
          >
            Stream License Key
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

      <Form.Group as={Row} className="mb-3" controlId="streamPath">
        <Form.Label column sm={4}>
          Path to your Stream installation directory:
        </Form.Label>
        <Col sm={8}>
          <Form.Control
            type="text"
            placeholder="Path to directory"
            required
            name="streamPath"
            onChange={handleInputChange}
          />
        </Col>
      </Form.Group>

      <Form.Group as={Row} className="mb-3">
        <Form.Label column sm={4}>
          Restart policy
        </Form.Label>
        <Col sm={8} className="mt-2 d-flex justify-content-between">
          <Form.Check
            type="radio"
            name="restart-policy"
            label='No (Docker Default)'
            id='rp1'
            value='no'
            onChange={handleInputChange}
          />
          <Form.Check
            type="radio"
            name="restart-policy"
            label='Unless Stopped'
            id='rp2'
            value='unless-stopped'
            onChange={handleInputChange}
          />
          <Form.Check
            type="radio"
            name="restart-policy"
            label='Always'
            id='rp3'
            value='always'
            onChange={handleInputChange}
          />
          <Form.Check
            type="radio"
            name="restart-policy"
            label='On Failure'
            id='rp4'
            value='on-failure'
            onChange={handleInputChange}
          />
        </Col>

      </Form.Group>

      <ShowCommand curlPort={""} command={command} validated={tokenValidated} />

      <Form.Group as={Row} className="mb-3">
        <div className="col-2">
          <Button
            onClick={handleConfigureClick}
            className="btn btn-success"
            type="button"
          >
            Configure
          </Button>
        </div>
        <label
          className="col-auto align-self-center form-label"
          htmlFor="button-submit-snapshot"
        >
          Edit configurations for your Stream license
        </label>
      </Form.Group>

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

      <Update isEnabled={true} image={STREAM_IMAGE} />
      <Uninstall isEnabled={true} image={STREAM_IMAGE} />
    </Form>
  );
}
