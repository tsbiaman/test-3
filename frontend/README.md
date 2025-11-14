# Deployment Lab Frontend

Thin React + Vite UI that pairs with the Flask backend in `LOCAL_3/backend` to visualize health, trigger simulated jobs, and smoke-test an end-to-end deployment stack.

## What you get

- Live health dashboard backed by `/api/health`
- Job simulator that POSTs to `/api/jobs` and streams Socket.IO updates
- Echo tester for `/api/echo`
- Real-time event feed connected to the backend's Socket.IO gateway

## Local development

```bash
cd LOCAL_3/frontend
npm install
npm run dev
```

By default Vite serves on `http://localhost:5173`. Configure a proxy to the backend or use environment variables (see below) to point to a remote API.

## Environment variables

Any variable prefixed with `VITE_` is exposed to the client. For example, create a `.env` with:

```
VITE_API_BASE_URL=http://localhost:8080/api
VITE_WS_URL=ws://localhost:8080
```

Access them from code via `import.meta.env.VITE_API_BASE_URL`.

## Production build

```bash
cd LOCAL_3/frontend
npm run build
npm run preview  # optional smoke test on http://localhost:3000
```

The compiled assets land in `dist/` and are ready to be served by any static web server.

## Docker image

Use the included multi-stage Dockerfile to produce an optimized image with Node.js serve:

```bash
cd LOCAL_3/frontend
docker build -t auto-deploy-frontend .
docker run -p 3000:3000 auto-deploy-frontend
```

The container uses `serve` to serve the static files with SPA routing support.

## Linting

```bash
npm run lint
```

Adjust `eslint.config.js` if you need stricter rules or type-aware analysis.
