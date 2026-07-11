# npm 10 on Node 22 intermittently crashes during `npm ci` in Docker
# (npm/cli#7666). Node 20 is supported by Remotion 4 and avoids that bug.
FROM node:20-bookworm-slim AS remotion-runtime

WORKDIR /app/remotion
COPY remotion/package.json remotion/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=secret,id=npm_ca \
    if [ -s /run/secrets/npm_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/npm_ca; fi \
    && npm ci --no-audit --no-fund \
    && npx remotion browser ensure

FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.2 \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

# Runtime tools plus the shared libraries required by Chrome Headless Shell.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    ffmpeg \
    git \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libgbm-dev \
    libnss3 \
    libpango-1.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon-dev \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

# Use the official Node.js runtime without Debian's large npm dependency tree.
COPY --from=remotion-runtime /usr/local/bin/node /usr/local/bin/node
COPY --from=remotion-runtime /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

RUN pip install "poetry==$POETRY_VERSION" \
    && poetry config virtualenvs.create false

WORKDIR /app

# Install each dependency layer before copying source code, preserving Docker's cache.
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction

COPY --from=remotion-runtime /app/remotion/node_modules ./remotion/node_modules
COPY src ./src
COPY remotion/package.json remotion/package-lock.json ./remotion/
COPY remotion/src ./remotion/src
COPY remotion/tsconfig.json ./remotion/tsconfig.json
RUN poetry install --only main --no-interaction

# Persist an optional corporate root CA for GitHub and AWS calls at runtime.
RUN --mount=type=secret,id=npm_ca \
    if [ -s /run/secrets/npm_ca ]; then \
        cp /run/secrets/npm_ca /usr/local/share/ca-certificates/corporate-root-ca.crt \
        && update-ca-certificates; \
    fi

# Avoid running cloned, untrusted repositories and Chromium as root.
ARG UID=1000
ARG GID=1000
RUN groupadd --gid "$GID" repodcast \
    && useradd --uid "$UID" --gid "$GID" --create-home repodcast \
    && mkdir -p /workspace /home/repodcast/.cache/repodcast \
    && chown -R repodcast:repodcast /workspace /home/repodcast

USER repodcast
WORKDIR /workspace

ENTRYPOINT ["repodcast"]
