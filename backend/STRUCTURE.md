# FastAPI application
.
├── app/
│   ├── main.py              Application entrypoint
│   ├── config.py            Pydantic settings
│   ├── database.py          SQLAlchemy engine / session
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── reports.py
│   │       ├── incidents.py
│   │       ├── uploads.py
│   │       └── auth.py
│   ├── core/
│   │   ├── security.py      JWT / password hashing
│   │   └── dependencies.py
│   ├── models/              SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── report.py
│   │   ├── incident.py
│   │   └── media_asset.py
│   ├── schemas/             Pydantic request/response
│   │   ├── report.py
│   │   ├── incident.py
│   │   └── user.py
│   ├── services/
│   │   ├── inference.py     ML worker orchestration
│   │   ├── duplicate.py     Near-duplicate detection
│   │   └── storage.py       Signed URL generation
│   └── workers/
│       ├── celery_app.py
│       └── inference_task.py
├── alembic/                 Database migrations
├── tests/
└── requirements.txt
