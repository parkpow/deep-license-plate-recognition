FROM --platform=$BUILDPLATFORM node:21.6-alpine3.18 AS client-builder
WORKDIR /ui
# cache packages in layer
COPY ui/package.json /ui/package.json
COPY ui/package-lock.json /ui/package-lock.json
RUN --mount=type=cache,target=/usr/src/app/.npm \
    npm set cache /usr/src/app/.npm && \
    npm ci
# install
COPY ui /ui
RUN npm run build


FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

LABEL org.opencontainers.image.title="Plate Recognizer Installer" \
    org.opencontainers.image.description="Plate Recognizer Installer" \
    org.opencontainers.image.vendor="Plate Recognizer" \
    com.docker.desktop.extension.api.version="0.3.4" \
    com.docker.extension.screenshots="" \
    com.docker.desktop.extension.icon="" \
    com.docker.extension.detailed-description="" \
    com.docker.extension.publisher-url="" \
    com.docker.extension.additional-urls="" \
    com.docker.extension.categories="" \
    com.docker.extension.changelog=""

RUN apt-get update\
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*\
    && pip install --upgrade pip

COPY docker-compose.yaml .
COPY metadata.json .
COPY logo.svg .

# Copy python dependecies file
COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
# Copy source code
COPY ./backend /app/


COPY --from=client-builder /ui/build ui
CMD ["gunicorn", "--workers", "1",  "--chdir", "/app", "--bind", "unix:/run/guest-services/backend.sock", "wsgi:app"]
