## Repository structure

```
.
├── backend/         FastAPI application, Alembic migrations
├── frontend/        Next.js app (App Router)
├── ml/              Training, inference, model cards
├── deployment/      Docker Compose, environment templates
└── .github/         CI workflows
```

## Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local backend development)
- Node.js 20+ (for local frontend development)

## Quick start

```bash
cp deployment/.env.example .env
docker compose -f deployment/docker-compose.yml up
```

## Development

See `backend/README.md` and `frontend/README.md` for dev setup.
