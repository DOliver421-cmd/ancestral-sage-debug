FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm ci --legacy-peer-deps

COPY . .

# Bake the backend URL into the React bundle at build time.
# Railway injects service variables as Docker build args automatically.
# REACT_APP_BACKEND_URL is already set in the Arts and Tech service Variables.
# Once baked in, the React app calls the backend directly — no nginx proxy needed.
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html

# Simple static file server — no proxy needed because the React app
# calls the backend directly via the baked-in REACT_APP_BACKEND_URL.
RUN echo 'server { \
    listen 8080; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { try_files $uri $uri/ /index.html; } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
