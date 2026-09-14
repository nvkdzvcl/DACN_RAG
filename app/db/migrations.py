"""Additive migrations for existing SQLite/PostgreSQL databases."""
from sqlalchemy import inspect, text
from app.db.session import Base
from app.models import support  # noqa: F401


def migrate(engine):
    # ponytail: additive schema only; use Alembic before destructive schema changes.
    with engine.begin() as connection:
        Base.metadata.create_all(connection)
        connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)"))
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
        if not connection.execute(text("SELECT version FROM schema_migrations WHERE version = 1")).first():
            connection.execute(text("UPDATE conversations SET status = 'handoff_requested' WHERE status = 'assigned' AND assigned_agent_id IS NULL"))
            connection.execute(text("UPDATE tickets SET status = 'open' WHERE status = 'assigned' AND conversation_id IN (SELECT id FROM conversations WHERE status = 'handoff_requested' AND assigned_agent_id IS NULL)"))
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES (1)"))
        additions = {
            "conversations": {"last_customer_message_id": "VARCHAR(64)"},
            "knowledge_documents": {"file_hash": "VARCHAR(64)", "index_version": "VARCHAR(64)", "embedding_model": "VARCHAR(160)"},
            "document_chunks": {"page": "INTEGER", "location": "VARCHAR(160)"},
        }
        for table, columns in additions.items():
            existing = {column["name"] for column in inspect(connection).get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_document_hash ON knowledge_documents (file_hash)"))
        if not connection.execute(text("SELECT version FROM schema_migrations WHERE version = 2")).first():
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES (2)"))
        if not connection.execute(text("SELECT version FROM schema_migrations WHERE version = 3")).first():
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES (3)"))
        existing = {column['name'] for column in inspect(connection).get_columns('tickets')}
        for name, definition in {'completed_at': 'TIMESTAMP', 'completed_by_id': 'VARCHAR(64) REFERENCES users(id)',
                                 'completion_note': 'TEXT', 'first_response_at': 'TIMESTAMP'}.items():
            if name not in existing:
                connection.execute(text(f'ALTER TABLE tickets ADD COLUMN {name} {definition}'))
        if not connection.execute(text("SELECT version FROM schema_migrations WHERE version = 4")).first():
            # Freeze observed legacy replies; completion time and actor remain unknown.
            connection.execute(text("""UPDATE tickets SET first_response_at = (
                SELECT MIN(messages.created_at) FROM messages WHERE messages.conversation_id = tickets.conversation_id
                AND messages.sender_type = 'agent' AND messages.agent_id IS NOT NULL AND messages.created_at >= tickets.created_at
            ) WHERE status IN ('closed', 'resolved')"""))
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES (4)"))
