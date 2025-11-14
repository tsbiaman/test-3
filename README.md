# LOCAL_3: Auto-Deployment Test Application

A full-stack application for testing automated deployment features with REST APIs, WebSockets, and multiple database integrations.

## Architecture

- **Backend**: Flask + Socket.IO (Python)
  - REST API endpoints for health checks, job simulation, and configuration
  - WebSocket support for real-time updates
  - Database connectors for MongoDB, Redis, and PostgreSQL
  - Docker containerized with multi-stage build

- **Frontend**: React + Vite (TypeScript)
  - Interactive dashboard for backend interaction
  - Real-time WebSocket event feed
  - Health monitoring and job queuing interface
  - Docker containerized with Node.js serve

## Deployment

This application is designed to deploy to the TSBI VPS ecosystem using automated workflows.

### GitHub Workflow

The `.github/workflows/deploy-local3.yml` follows the registry-based deployment pattern:

1. **Test Job**: Runs backend pytest and frontend linting
2. **Build & Push Job**: Builds Docker images and pushes to `registry.tsbi.fun`
3. **Deploy Job**: Deploys from registry to VPS using `deploy-from-registry.sh`

### Site Configuration

- **Backend Site ID**: `local-3` (matches repository name)
- **Frontend Site ID**: `local-3-frontend`
- **Registry**: `registry.tsbi.fun`
- **Image Names**: `local-3-backend`, `local-3-frontend`

### Environment Variables

Backend requires these environment variables (set in VPS ecosystem):
- `MONGODB_URL`
- `REDIS_URL`
- `POSTGRES_URL`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

### GitHub Secrets Required

- `TSBI_HOST` - VPS hostname
- `TSBI_USER` - SSH username
- `TSBI_SSH_KEY` - Private SSH key for deployment
- `REGISTRY_USER` - Container registry username
- `REGISTRY_PASSWORD` - Container registry password</content>
<parameter name="filePath">/home/aman/Desktop/Deploy_Ecosystem/LOCAL_3/README.md
