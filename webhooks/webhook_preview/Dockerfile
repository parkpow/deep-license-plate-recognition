# syntax=docker/dockerfile:1

FROM node:18-alpine AS base

# Instala dependências necessárias
RUN apk add --no-cache libc6-compat

# Configura pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Define o diretório de trabalho
WORKDIR /app

# Build
FROM base AS builder

# Configura pnpm e ambiente
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
ENV NODE_OPTIONS="--max-old-space-size=4096"


# Copia arquivos de configuração
COPY package.json pnpm-lock.yaml ./
COPY prisma ./prisma/

# Instala dependências
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --no-frozen-lockfile

# Gera cliente Prisma
RUN pnpm prisma generate

# Copia arquivos do projeto
COPY . .

# Build da aplicação
RUN pnpm build

# Runner
FROM base AS runner

WORKDIR /app

# Cria usuário não-root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copia arquivos com permissões corretas
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/prisma ./prisma
COPY --from=builder --chown=nextjs:nodejs /app/generated ./generated

USER nextjs

# Configurações do ambiente
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

EXPOSE 3000

CMD ["node", "server.js"]