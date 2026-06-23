#!/usr/bin/env python
"""Apply schema.sql to create/update the local SQLite database."""
from clip_farmer.db.database import init_db
from clip_farmer.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    init_db(settings.db_path)
    print(f"Database initialized at {settings.db_path}")
