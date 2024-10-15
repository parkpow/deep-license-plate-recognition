# Plate Recognizer Installer

Plate Recognizer Installer Docker extension.

This extension is composed of:

- A [frontend](./ui) app in React.
- A [backend](./backend) container that runs an API in Python. Makes request to verify token

## Local development

You can use `docker` to build, install and push your extension. Also, we provide an opinionated [Makefile](Makefile) that could be convenient for you. There isn't a strong preference of using one over the other, so just use the one you're most comfortable with.

To build the extension, use `make build-extension` **or**:

```shell
  docker buildx build -t platerecognizer/installer:latest . --load
```

To install the extension, use `make install-extension` **or**:

```shell
  docker extension install platerecognizer/installer:latest
```

> If you want to automate this command, use the `-f` or `--force` flag to accept the warning message.

To preview the extension in Docker Desktop, open Docker Dashboard once the installation is complete. The left-hand menu displays a new tab with the name of your extension. You can also use `docker extension ls` to see that the extension has been installed successfully.

### Frontend development

During the development of the frontend part, it's helpful to use hot reloading to test your changes without rebuilding your entire extension. To do this, you can configure Docker Desktop to load your UI from a development server.
Assuming your app runs on the default port, start your UI app and then run:

```shell
  cd ui
  npm install
  npm run dev
```

This starts a development server that listens on port `3000`.

You can now tell Docker Desktop to use this as the frontend source. In another terminal run:

```shell
  docker extension dev ui-source platerecognizer/installer:latest http://localhost:3000
```

In order to open the Chrome Dev Tools for your extension when you click on the extension tab, run:

```shell
  docker extension dev debug platerecognizer/installer:latest
```

Each subsequent click on the extension tab will also open Chrome Dev Tools. To stop this behaviour, run:

```shell
  docker extension dev reset platerecognizer/installer:latest
```

### Backend development

Whenever you make changes in the [backend](./backend) source code, you will need to compile them and re-deploy a new version of your backend container.
Use the `docker extension update` command to remove and re-install the extension automatically:

```shell
docker extension update platerecognizer/installer:latest
```

> If you want to automate this command, use the `-f` or `--force` flag to accept the warning message.

> Extension containers are hidden from the Docker Dashboard by default. You can change this in Settings > Extensions > Show Docker Extensions system containers.

### Clean up

To remove the extension:

```shell
docker extension rm platerecognizer/installer:latest
```

## What's next?

- To learn more about how to build your extension refer to the Extension SDK docs at <https://docs.docker.com/desktop/extensions-sdk/>.
- To publish your extension in the Marketplace visit <https://www.docker.com/products/extensions/submissions/>.
- To report issues and feedback visit <https://github.com/docker/extensions-sdk/issues>.
- To look for other ideas of new extensions, or propose new ideas of extensions you would like to see, visit <https://github.com/docker/extension-ideas/discussions>.
