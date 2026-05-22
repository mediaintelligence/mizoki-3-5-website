# MIZOKI3 React + Vite site — multi-stage build, served by nginx on Cloud Run.

# ---- Stage 1: build the React app with Vite ----
FROM node:20-alpine AS build
WORKDIR /app

# Install deps first for better layer caching
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

# Build the static bundle into /app/dist
COPY . .
RUN npm run build

# ---- Stage 2: serve the static dist with nginx (Cloud Run port 8080) ----
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
