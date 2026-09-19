"""Alembic migration script configuration.

This file is used by Alembic to generate migration scripts.
Run: alembic revision --autogenerate -m "description"
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import all models so Alembic sees them
from app.models import *  # noqa: F401,F403
from app.database import Base  # noqa: E402
