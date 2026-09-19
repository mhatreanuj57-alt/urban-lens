# UrbanLens AI

A civic-intelligence platform for Navi Mumbai. Citizens submit road photos or short videos; AI turns them into structured reports, maps recurring issues, and helps an operations team prioritise response.

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Maps | MapLibre GL + OpenStreetMap |
| API | FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL 16 + PostGIS + pgvector |
| Queue/cache | Redis + Celery |
| Media storage | Cloudflare R2 / MinIO |
| Detection | YOLO, PyTorch, OpenCV |
| Embeddings | CLIP / SigLIP |
| Forecasting | LightGBM |

## Repo layout

```
├── backend/         FastAPI application, Alembic migrations
├── frontend/        Next.js app (App Router)
├── ml/              Training, inference, model cards
├── deployment/      Docker Compose, environment templates
└── .github/         CI workflows
```

## Quick start

```bash
cp deployment/.env.example .env
docker compose -f deployment/docker-compose.yml up
```

## Development

See `backend/README.md` and `frontend/README.md` for dev setup.

## License

MIT
