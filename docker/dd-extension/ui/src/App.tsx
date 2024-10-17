import React from "react";
import {
  Container,
} from "react-bootstrap";


import Tab from "react-bootstrap/Tab";
import Tabs from "react-bootstrap/Tabs";

import Stream from "./components/Stream";
import Snapshot from "./components/Snapshot";


export function App() {

  return (
    <Container>
      <h2 className="text-center">Plate Recognizer Installer</h2>
      <Tabs defaultActiveKey="stream" className="mb-3 justify-content-center">
        <Tab eventKey="stream" title="Stream">
          <Stream />
        </Tab>
        <Tab eventKey="snapshot" title="Snapshot">
          <Snapshot />
        </Tab>

      </Tabs>
    </Container>
  );
}
