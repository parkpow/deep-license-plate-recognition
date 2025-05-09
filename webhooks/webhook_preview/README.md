# License Plate Webhook Dashboard

A webhook dashboard for license plate recognition data from Stream.

## 🧰 Technologies Used

- **Next.js** – Full-stack React framework
- **Prisma** – ORM for database access
- **PostgreSQL** – Relational database for persistent data
- **Cloudflare R2** – Object storage for image uploads
- **pnpm** – Fast package manager

# 🛠️ Project Setup Guide

Follow these steps to set up and run the project locally.

---

## 1. Clone the Repository

```bash
git clone https://github.com/parkpow/deep-license-plate-recognition.git

cd /webhooks/webhook_preview
```

---

## 2. Install Dependencies

Use `pnpm` to install the project dependencies:

```bash
pnpm install
```

If you don't have `pnpm` installed yet:

```bash
npm install -g pnpm
```

---

## 3. Configure Environment Variables

Create a `.env` file in the root of the project and add the required environment variables.

You can use the `.env.example` file as a template. Just copy it and fill in the appropriate values:

```bash
cp .env.example .env
```

Example `.env` content:

```env
# PostgreSQL connection string
DATABASE_URL="postgresql://user:password@localhost:5432/your_database?schema=public"
```

Used by Prisma to connect to your PostgreSQL database.

```env
# Limits the number of simultaneous webhook requests that can be handled
NEXT_PUBLIC_MAX_WEBHOOK_REQUESTS=100
```

This variable defines the maximum number of webhook requests stored in memory. Helps control resource usage.

```env
# Cloudflare R2 credentials and configuration
CLOUDFLARE_R2_ACCOUNT_ID=your_account_id
CLOUDFLARE_R2_ACCESS_KEY_ID=your_access_key_id
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_secret_access_key
CLOUDFLARE_R2_BUCKET_NAME=your_bucket_name
CLOUDFLARE_R2_PUBLIC_DOMAIN=https://your-bucket-name.r2.dev
```

These are required to upload and retrieve image files from Cloudflare R2 object storage.

---

## 4. Start PostgreSQL with Docker

If you don't have a local PostgreSQL server running, you can start one using Docker:

```bash
docker run --name license-db -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=your_database -p 5432:5432 -d postgres
```

Update your `.env` file to match the database credentials:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/your_database?schema=public"
```

---

## 5. Set Up the Database

Run the following command to apply the initial database migration using Prisma:

```bash
npx prisma generate

npx prisma migrate dev --name init
```

This will create the necessary tables in your database and generate the Prisma client to use in your application.

---

## 6. Start the Development Server

Finally, start the development server with:

```bash
pnpm run dev
```

The application should now be running at:

```
http://localhost:3000
```

---

## 7. Running with Docker

You can also run the entire application using Docker Compose, which will set up both the application and the PostgreSQL database in containers.

### Prerequisites

- Docker and Docker Compose installed on your system
- Make sure the environment variables in the docker-compose.yml file are properly configured for your environment, including the Cloudflare R2 credentials and the webhook request limit (as described in step 3).

### Steps to Run with Docker

1. **Build and start the containers:**

- In your terminal, navigate to the root of the project and run the command below.

```bash
docker-compose up -d --build
```

This command builds the Docker images and starts the containers in detached mode.

2. **Check the logs to ensure everything is running correctly:**

```bash
docker-compose logs -f
```

3. **Access the application:**

The application will be available at:

```
http://localhost:3000
```

### Important Notes for Docker Deployment

- The `docker-compose.yml` file is configured to pass environment variables to both the build process and runtime environment.
- The PostgreSQL data is persisted in a Docker volume named `postgres_data`.

### Stopping the Docker Containers

To stop the running containers:

```bash
docker-compose down
```

To stop the containers and remove the volumes (this will delete all database data):

```bash
docker-compose down -v
```

---

## Usage

1. Visit the homepage to generate a new webhook URL
2. Use the generated URL to config webhook send in Stream
3. View the data in on the dashboard
4. Access your data anytime by visiting `/{uuid}`, where `{uuid}` is your webhook UUID

### 🔧 Using Prisma Studio in Development

You can use Prisma Studio to visually inspect and manage your database. To start it, run:

```bash
pnpm prisma studio
```

Prisma Studio provides a web interface for easy database management, useful for debugging and quick edits during development.
