FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm ci --legacy-peer-deps

COPY . .

RUN npm run build

FROM nginx:alpine

# React build output
COPY --from=builder /app/build /usr/share/nginx/html

# nginx config template — BACKEND_URL is substituted at container startup
# so the image can be reused across environments without a rebuild.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Entrypoint: runs envsubst on the template, then starts nginx
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
