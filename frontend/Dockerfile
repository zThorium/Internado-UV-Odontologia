# Etapa 1: build
FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_URL
ARG VITE_RECAPTCHA_SITE_KEY
ARG VITE_WARN_INSECURE_CONNECTION
ARG VITE_KEYCLOAK_URL
ARG VITE_KEYCLOAK_REALM
ARG VITE_KEYCLOAK_CLIENT_ID

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_RECAPTCHA_SITE_KEY=$VITE_RECAPTCHA_SITE_KEY
ENV VITE_WARN_INSECURE_CONNECTION=$VITE_WARN_INSECURE_CONNECTION
ENV VITE_KEYCLOAK_URL=$VITE_KEYCLOAK_URL
ENV VITE_KEYCLOAK_REALM=$VITE_KEYCLOAK_REALM
ENV VITE_KEYCLOAK_CLIENT_ID=$VITE_KEYCLOAK_CLIENT_ID

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Etapa 2: servidor estático con nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Configuración nginx para SPA (React Router)
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location /api/ {\n\
        proxy_pass http://backend:8000/;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
    }\n\
    location = /api {\n\
        proxy_pass http://backend:8000;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
    }\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
