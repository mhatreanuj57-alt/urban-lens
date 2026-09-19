# UrbanLens AI — Backend

FastAPI application for the UrbanLens civic intelligence platform.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## API docs

Visit `/docs` (Swagger UI) once running.

## Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Testing

```bash
pytest
```
