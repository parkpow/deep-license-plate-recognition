# License Plate Webhook Dashboard

A webhook dashboard for license plate recognition data.

# 🛠️ Project Setup Guide

Follow these steps to set up and run the project locally.

---

## 1. Clone the Repository

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

Create a `.env` file in the root of the project and add the required environment variables. Example:

```env
# PostgreSQL database connection string
DATABASE_URL="postgresql://user:password@localhost:5432/your_database?schema=public"

# Maximum number of simultaneous webhook requests allowed
NEXT_PUBLIC_MAX_WEBHOOK_REQUESTS=100

# Cloudflare R2 configuration
CLOUDFLARE_R2_ACCOUNT_ID=your_account_id
CLOUDFLARE_R2_ACCESS_KEY_ID=your_access_key_id
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_secret_access_key
CLOUDFLARE_R2_BUCKET_NAME=your_bucket_name
CLOUDFLARE_R2_PUBLIC_DOMAIN=https://your-bucket-name.r2.dev
```

## 4. Set Up the Database

Run the following command to apply the initial database migration using Prisma:

```bash
pnpx prisma migrate dev --name init
```

This will create the necessary database schema and generate the Prisma client.

---

## 5. Start the Development Server

Finally, start the development server with:

```bash
pnpm run dev
```

The application should now be running at:

```
http://localhost:3000
```

---

## Usage

1. Visit the homepage to generate a new webhook URL
2. Use the generated URL to send license plate recognition data
3. View the data in real-time on the dashboard
4. Access your data anytime by visiting `/{uuid}` where `{uuid}` is your webhook UUID
