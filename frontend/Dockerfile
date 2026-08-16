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
# BACKEND_URL — full URL of the backend service. The default fits the
# home-server compose (`backend` service); on Railway set this to the
# backend service's URL (e.g. https://backend-production.up.railway.app).
ENV BACKEND_URL=http://backend:8080

# 15-backend-host.sh derives BACKEND_HOST from BACKEND_URL (when not
# explicitly set) BEFORE the image's envsubst step, so the template never
# renders an undefined variable. The chmod guards against non-executable
# bits from the git checkout.
COPY docker-entrypoint.d/ /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/*.sh

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
