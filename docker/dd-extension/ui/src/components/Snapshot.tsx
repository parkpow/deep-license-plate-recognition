import {
  Row,
  Col,
  Button,
} from "react-bootstrap";

import Form from "react-bootstrap/Form";

import React, { useState, useEffect } from "react";
import { useDockerDesktopClient } from "../hooks/useDockerDesktopClient";
import Loader from "./Loader";
import Uninstall from "./Uninstall";
import Update from "./Update";
import ShowCommand from "./ShowCommand";
import { openBrowserUrl } from '../helpers'

const countryOptions = [
  { value: '', label: 'Select country' },
  { value: 'Global', label: 'Global' },
  { value: 'egypt', label: 'Egypt' },
  { value: 'germany', label: 'Germany' },
  { value: 'japan', label: 'Japan' },
  { value: 'korea', label: 'Korea' },
  { value: 'thailand', label: 'Thailand' },
  { value: 'uae', label: 'United Arab Emirates' },
];

const architectureOptionsSnapshot = [
  { value: 'alpr', label: 'Intel x86 or amd64(x64)' },
  { value: 'alpr-no-avx', label: 'Intel x86 or amd64(x64) no-avx' },
  { value: 'alpr-gpu', label: 'Intel x86 or amd64(x64) with Nvidia GPU' },
  { value: 'alpr-arm', label: 'ARM based CPUs, Raspberry Pi or Apple M1' },
  { value: 'alpr-jetson', label: 'Nvidia Jetson (with GPU) for Jetpack 4.6 (r32)' },
  { value: 'alpr-jetson:r35', label: 'Nvidia Jetson (with GPU) for Jetpack 5.x (r35)' },
  { value: 'alpr-zcu104', label: 'ZCU' },
];


export default function Snapshot() {
  const [licenseKey, setLicenseKey] = useState('');
  const [token, setToken] = useState('');
  const [tokenValidated, setTokenValidated] = useState(false);
  const [isLoading, setLoading] = useState(false);

  const [command, setCommand] = useState<string>("");
  const [curlPort, setCurlPort] = useState("8080");
  const [dockerimage, setDockerimage] = useState('');
  const [country, setCountry] = useState('Global');
  const [architecture, setArchitecture] = useState('alpr');
  const [restartPolicy, setRestartPolicy] = useState('no');

  const ddClient = useDockerDesktopClient();

  const handleInputChange = (e: any) => {
    setTokenValidated(false);
    const { name, value } = e.target;
    if (name == "license") {
      setLicenseKey(value);
    } else if (name == "token") {
      setToken(value)
    } else if (name == "port") {
      setCurlPort(value);
    } else if (name == "restart-policy") {
      setRestartPolicy(value);
    }
  };

  const handleArchitectureChange = (e:any) => {
    setTokenValidated(false);
    setArchitecture(e.target.value);
  };


  interface SnapshotData {
    port: string;
    license: string;
    token: string;
    image: string;
  }
  const generateDockerImage = () => {
    let dockerImage = 'platerecognizer/';
    if (country === 'Global' || architecture === 'alpr-jetson:r35' || architecture === 'alpr-no-avx') {
      dockerImage += `${architecture}`;
    } else {
      dockerImage += `${architecture}:${country}`;
    }
    setDockerimage(dockerImage)
    return (dockerImage)
  };
  const generateDockerRunCommand = (dockerImage:any) => {
    let restartOption;
    switch (restartPolicy) {
      case 'no':
        restartOption = ''
        break
      default:
        restartOption = `--restart=${restartPolicy} `
        break
    }
    const baseCommand = `docker run ${restartOption}-t -p ${curlPort}:8080 -v license:/license`;
    let platformSpecificCommand = '';

    switch (architecture) {
      case 'alpr-jetson':
      case 'alpr-jetson:r35':
        platformSpecificCommand = ` --runtime nvidia -e LICENSE_KEY=${licenseKey} -e TOKEN=${token}   ${dockerImage}`;
        break;
      case 'alpr-gpu':
        platformSpecificCommand = ` --gpus all -e LICENSE_KEY=${licenseKey} -e TOKEN=${token}  ${dockerImage}`;
        break;
      case 'alpr':
      case 'alpr-no-avx':
      case 'alpr-arm':
      case 'alpr-zcu104':
        platformSpecificCommand = `  -e LICENSE_KEY=${licenseKey} -e TOKEN=${token}  ${dockerImage}`;
        break;
      default:
        break;
    }

    setCommand(`${baseCommand} ${platformSpecificCommand}`);

  };

  useEffect(() => {
    const imagem = generateDockerImage()
    generateDockerRunCommand(imagem)
  }, [country, architecture, token, licenseKey, restartPolicy]);


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
          ddClient.docker.cli.exec("pull", [dockerimage]).then((result) => {
            setTokenValidated(valid);
            setLoading(false);
          });
        } else {
          setLoading(false);
          ddClient.desktopUI.toast.error(`Verify Token: ${message}`);
        }
      });
  };
  const handleCountryChange = (e: any) => {
    setTokenValidated(false);
    setCountry(e.target.value);
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
          <a href="https://app.platerecognizer.com/service/snapshot-sdk/" onClick={handleLinkClick}>
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

      <Form.Group as={Row} className="mb-3">
        <Form.Label column sm={4}>
          Restart policy
        </Form.Label>
        <Col sm={8} className="mt-2 d-flex justify-content-between">
          <Form.Check
            type="radio"
            name="restart-policy"
            label='No (Docker Default)'
            id='rps1'
            value='no'
            checked={restartPolicy == 'no'}
            onChange={handleInputChange}
          />
          <Form.Check
            type="radio"
            name="restart-policy"
            label='Unless Stopped'
            id='rps2'
            value='unless-stopped'
            onChange={handleInputChange}
          />
          <Form.Check
            type="radio"
            name="restart-policy"
            label='Always'
            id='rps3'
            value='always'
            onChange={handleInputChange}
          />
          <Form.Check
            type="radio"
            name="restart-policy"
            label='On Failure'
            id='rps4'
            value='on-failure'
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
        <Col sm={3}>
          <Form.Select
            aria-label="Snapshot Docker Image Country"
            onChange={handleCountryChange}
            name="country"
            defaultValue={country}
            disabled={architecture === 'alpr-jetson:r35' || architecture === 'alpr-no-avx'}
          >
            {countryOptions.map((option, index) => (
              <option key={index} value={option.value}>
                {option.label}
              </option>
            ))}
          </Form.Select>
        </Col>
        <Col sm={5}>
          <Form.Select
            aria-label="Snapshot Docker Image"
            onChange={handleArchitectureChange}
            name="image"
            defaultValue={architecture}
          >
            {architectureOptionsSnapshot.map((option, index) => (
              <option key={index} value={option.value}>
                {option.label}
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

      <Update isEnabled={true} image={dockerimage} />
      <Uninstall isEnabled={true} image={dockerimage} />
    </Form>
  );
}
