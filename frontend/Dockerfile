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

FROM node:20-alpine
WORKDIR /app

# Install serve globally for serving static files
RUN npm install -g serve

COPY --from=build /app/dist /app/dist

CMD ["serve", "-s", "dist"]
