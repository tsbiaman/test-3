# syntax=docker/dockerfile:1

FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY public ./public
COPY src ./src

RUN npm ci
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

# EXPOSE 4173
CMD ["nginx", "-g", "daemon off;"]
