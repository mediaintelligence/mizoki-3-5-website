# Installation Instructions

## 1. Unzip the package

```bash
unzip mizoki3-final-production-pages.zip
cd mizoki3-final-production-pages
```

## 2. Install Node.js

Use Node.js 20+.

Check your version:

```bash
node -v
npm -v
```

## 3. Install dependencies

```bash
npm install
```

## 4. Run locally

```bash
npm run dev
```

Vite will print a local URL, usually:

```text
http://localhost:5173
```

Open that URL in your browser.

## 5. Build for production

```bash
npm run build
```

The production files will be created in:

```text
dist/
```

## 6. Preview production build

```bash
npm run preview
```

## 7. Deploy

### Vercel

```bash
npm install -g vercel
vercel
```

Use:
- Framework: Vite
- Build command: `npm run build`
- Output directory: `dist`

### Netlify

Use:
- Build command: `npm run build`
- Publish directory: `dist`

### Cloud Run

Build with Docker or serve `dist/` through an Nginx container. See `DEPLOYMENT.md`.
