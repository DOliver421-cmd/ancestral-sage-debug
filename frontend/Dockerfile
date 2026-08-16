# Frontend image — used ONLY for a split frontend/backend deployment.
# The primary deployment (root Dockerfile) builds the React app into the
# backend image, where the backend serves the SPA and /api same-origin —
# in that topology this image is not used.
#
# When split mode IS used, nginx serves the SPA and proxies /api/* to the
# backend service so the React app can call same-origin URLs (no CORS, no
# baked-in dead host). BACKEND_URL defaults to the home-server compose
# backend service; override for other topologies (e.g. a Railway backend).
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm ci --legacy-peer-deps

ARG CACHE_BUST=20260816
COPY . .

# Build-time URL for any code that reads REACT_APP_BACKEND_URL directly.
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# nginx runs envsubst on /etc/nginx/templates/*.template at boot.
# BACKEND_URL — full URL of the backend service (e.g. https://foo.up.railway.app).
#
# The DEFAULT is deliberately an unreachable IP literal (127.0.0.1:9), NOT a
# hostname. nginx resolves proxy_pass hostnames at STARTUP and aborts with
# "host not found in upstream" if they don't resolve — the compose-only name
# `backend:8080` used to be the default, which killed every Railway deploy the
# moment BACKEND_URL wasn't set. An IP literal needs no DNS, so nginx ALWAYS
# starts, the healthcheck always passes, and the SPA is always served; /api
# calls return 502 until you set BACKEND_URL to the real backend.
# Home-server compose users: set BACKEND_URL=http://backend:8080 explicitly.
ENV BACKEND_URL=http://127.0.0.1:9

# 15-backend-host.envsh derives BACKEND_HOST from BACKEND_URL (when not
# explicitly set) BEFORE the image's envsubst step. It must be an .envsh
# (sourced) rather than .sh (executed as a child process) — the image's
# entrypoint sources .envsh files into its own shell, so the export actually
# reaches 20-envsubst-on-templates.sh. The chmod guards against
# non-executable bits from the git checkout (both kinds require +x).
COPY docker-entrypoint.d/ /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/*.sh /docker-entrypoint.d/*.envsh

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
