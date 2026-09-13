"""Additive migrations for existing SQLite/PostgreSQL databases."""
from sqlalchemy import inspect, text
from app.db.session import Base
from app.models import support  # noqa: F401


def migrate(engine):
    # ponytail: additive schema only; use Alembic before destructive schema changes.
    with engine.begin() as connection:
        Base.metadata.create_all(connection)
        connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)"))
        if connection.execute(text("SELECT version FROM schema_migrations WHERE version = 1")).first():
            return
        additions = {
            "conversations": {"assigned_agent_id": "VARCHAR(64) REFERENCES users(id)"},
            "messages": {"agent_id": "VARCHAR(64) REFERENCES users(id)", "citations": "JSON"},
        }
        for table, columns in additions.items():
            existing = {column["name"] for column in inspect(connection).get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
        # Old demo assignments have no authenticated owner; return them to the queue.
        connection.execute(text("UPDATE conversations SET status = 'handoff_requested' WHERE status = 'assigned' AND assigned_agent_id IS NULL"))
        connection.execute(text("UPDATE tickets SET status = 'open' WHERE status = 'assigned' AND conversation_id IN (SELECT id FROM conversations WHERE status = 'handoff_requested' AND assigned_agent_id IS NULL)"))
        connection.execute(text("INSERT INTO schema_migrations (version) VALUES (1)"))
