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
ENV BACKEND_URL=http://backend:8080

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
