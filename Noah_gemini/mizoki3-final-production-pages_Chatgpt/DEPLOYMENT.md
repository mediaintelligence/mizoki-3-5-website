# Deployment Guide

## Vercel

1. Push this folder to GitHub.
2. Import the repo into Vercel.
3. Use:
   - Framework: Vite
   - Build command: `npm run build`
   - Output directory: `dist`
4. Deploy.

## Netlify

1. Push this folder to GitHub.
2. Import into Netlify.
3. Use:
   - Build command: `npm run build`
   - Publish directory: `dist`

## Google Cloud Run

### Option A: static Nginx container

Create this `Dockerfile` in the project root:

```Dockerfile
FROM node:20 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
```

Create `nginx.conf`:

```nginx
server {
  listen 8080;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }
}
```

Build and deploy:

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/mizoki3-site
gcloud run deploy mizoki3-site   --image gcr.io/YOUR_PROJECT_ID/mizoki3-site   --platform managed   --region us-central1   --allow-unauthenticated
```

## Notes

Because this is a React SPA using BrowserRouter, server rewrites should point all page refreshes to `index.html`.
