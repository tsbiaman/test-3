# Auto-Deployment Lab Backend

A single Flask backend that exercises the most common deployment touchpoints in one place:

- REST APIs (health, echo, job queue simulation)
- WebSockets for live status pushes (Flask-SocketIO)
- Connectivity hooks for MongoDB, Redis, and PostgreSQL
- Environment-driven configuration to mirror production rollouts

Use it to validate CI/CD automation, smoke test infrastructure, or demo rollout orchestration spanning multiple data services.

## Features

| Capability | Description |
|------------|-------------|
| `/api/health` | Summaries of each database connector with counters and timestamps. |
| `/api/db/<name>/status` | Targeted insight for one data store (`mongo`, `redis`, `postgres`). |
| `/api/jobs` | Simulates creating a deployment job and broadcasts it over WebSockets. |
| `/api/echo` | Round-trip payload test for REST clients and ingress filters. |
| WebSocket `health:update` | Push health snapshots on demand or at fixed intervals. |

## Quick start

```bash
cd LOCAL_3/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # adjust credentials or leave blank to skip live checks
python main.py
```

Local development
-----------------

To avoid exporting `.env` manually every time you run the backend locally, the app will automatically load `.env` when running `python main.py` if `python-dotenv` is installed. That means you can start services in Docker (redis/postgres/mongo), ensure their ports are published (e.g. `6379`, `5432`, `27017`), and run the backend with `python main.py` from this directory.

If you prefer to export environment variables in the current shell, run:

```bash
set -o allexport; source .env; set +o allexport
```

Browse `https://local-3-backend.tsbi.fun/api/health` or connect a Socket.IO client to `ws://localhost:8080`.

### Docker

```bash
cd LOCAL_3/backend
docker build -t auto-deploy-lab .
docker run --env-file .env -p 8080:8080 auto-deploy-lab
```

## Environment variables

See `.env.example` for the full list. Leaving a section blank simply marks that connector as `skipped`, which is safe for dry runs.

## Testing

```bash
cd LOCAL_3/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Deployment Notes

- WebSocket broadcasting uses Redis if `REDIS_URL` is defined, else it falls back to in-process events.
- Background health pushes can be disabled (e.g., for unit tests) with `ENABLE_BACKGROUND_TASKS=false`.
- Gunicorn/eventlet are included, so you can run `gunicorn -k eventlet main:app` in production if preferred.
