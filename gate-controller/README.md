# GateController

GateController takes API from an external source and triggers a gate's dry contact to open.

## About The Project

This application is built using a modern stack that combines a Rust backend with a web-based frontend.

- **Backend:** [Rust](https://www.rust-lang.org/) with [Tauri](https://tauri.app/)
- **Frontend:** [Next.js](https://nextjs.org/) (React) with [TypeScript](https://www.typescriptlang.org/)
- **UI:** [shadcn/ui](https://ui.shadcn.com/) & [Tailwind CSS](https://tailwindcss.com/)
- **Package Manager:** [Bun](https://bun.sh/)

## Prerequisites

Before you begin, ensure you have the following installed on your system.

1.  **Rust:** You need the Rust programming language and its toolchain (Cargo). You can install it via [rustup](https://rustup.rs/).
2.  **Node.js:** Required for the frontend environment. Download it from [nodejs.org](https://nodejs.org/).
3.  **Bun:** This project uses Bun as the package manager. Install it from [bun.sh](https://bun.sh/).
4.  **Tauri System Dependencies:** Tauri has specific system dependencies for building applications. Please follow the official guide for your operating system:
    - [Tauri Prerequisites Guide](https://tauri.app/v1/guides/getting-started/prerequisites)

## Getting Started (Development)

To get a local copy up and running for development, follow these steps.

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/parkpow/deep-license-plate-recognition.git
    cd gate-controller
    ```

2.  **Install Frontend Dependencies:**
    This command will install all the necessary Node.js packages defined in `package.json`.

    ```sh
    bun install
    ```

3.  **Run in Development Mode:**
    This command starts the Next.js development server and the Tauri application in a single process with hot-reloading.
    ```sh
    bun tauri dev
    ```

## Build and Production

To create a final, distributable application for your platform, follow these steps.

1.  **Build the Application:**
    This command bundles the frontend and compiles the Rust backend into a single executable.

    ```sh
    bun tauri build
    ```

2.  **Locate the Executable:**
    Once the build is complete, you can find the application executable (e.g., `.exe` on Windows) inside the `src-tauri/target/release/` directory.
