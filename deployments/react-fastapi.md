# React + FastAPI standalone deployment

This service is intentionally separate from the existing Streamlit deployment.
It serves the Vite-built React application and the existing FastAPI endpoints
from one container. It does not replace or modify the Streamlit Docker command.

## Build

Run from the repository root (the build context must be the repository root):

```bash
docker build -f Dockerfile.api -t eros-react-api .
```

The image uses Node 22 to build the locked frontend dependencies and Python
3.13 with the repository's locked runtime dependencies. Frontend lifecycle
scripts are disabled during installation. The final image runs as an
unprivileged user.

## Run locally

```bash
docker run --rm -p 8000:8000 eros-react-api
```

Open http://localhost:8000. Check http://localhost:8000/health and
http://localhost:8000/docs. The container honours the hosting platform's
`PORT` environment variable and defaults to port 8000.

## Deployment settings

- Build command: `docker build -f Dockerfile.api -t eros-react-api .`
- Dockerfile path: `Dockerfile.api`
- Build context: repository root (`.`)
- HTTP service port: `8000` (or the platform-provided `PORT`)
- Health check: `/health`
- Start command: provided by the Dockerfile; do not override unless required
  by the hosting platform.

Keep provider credentials and API tokens in the hosting platform's server-side
secret manager. Do not put credentials in React source or Vite variables
prefixed with `VITE_`. Configure only the secrets required by the selected
data providers and application features.

## Staging acceptance checklist

1. Confirm `/health` returns HTTP 200.
2. Confirm `/` serves the React app and its `/assets/*` files.
3. Confirm `/docs` and the existing `/api/v1/*` routes remain reachable.
4. Exercise read-only market endpoints outside market hours first.
5. During market hours, measure request latency, provider errors, worker
   saturation, and refresh behaviour before enabling frequent polling.
6. Keep the existing Streamlit service live until staging has passed.

The container workflow builds this image and smoke-tests health, React static
serving, and API documentation on relevant pull requests and pushes to main.
