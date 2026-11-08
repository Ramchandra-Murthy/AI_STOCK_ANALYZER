# EROS React dashboard

The React application is an independent presentation layer. It calls the existing
FastAPI endpoints and does not duplicate stock-scoring or signal calculations.

## Local development

From the repository root, in separate terminals:

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
cd frontend
npm ci --ignore-scripts
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/health` and `/api/*` to FastAPI.

## Production build

```bash
cd frontend
npm ci --ignore-scripts
npm run build
```

The build is written to `frontend/dist`. When that directory exists, FastAPI
serves the React entry page at `/` and the hashed assets at `/assets/*`.
When no production build exists, the existing EROS static dashboard remains
the fallback. API routes are registered before the frontend static fallback.

## Deployment boundary

Do not replace the current Streamlit deployment or its Docker command as part
of the React rollout. Deploy the API/frontend as a separate service first,
verify health and scan endpoints, then point the React UI at that API. Keep
provider credentials server-side; never place secrets in Vite environment
variables prefixed with `VITE_`.
