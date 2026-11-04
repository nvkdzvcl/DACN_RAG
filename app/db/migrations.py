"""Additive migrations for existing SQLite/PostgreSQL databases."""
from sqlalchemy import inspect, text
from app.db.session import Base
from app.models import support  # noqa: F401


def migrate(engine):
    # ponytail: additive schema only; use Alembic before destructive schema changes.
    with engine.begin() as connection:
        if engine.dialect.name == "sqlite":
            connection.execute(text("PRAGMA foreign_keys=ON"))
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
        if 'tool_trace' not in {c['name'] for c in inspect(connection).get_columns('messages')}:
            connection.execute(text('ALTER TABLE messages ADD COLUMN tool_trace JSON'))
        if not connection.execute(text('SELECT version FROM schema_migrations WHERE version = 5')).first():
            connection.execute(text('INSERT INTO schema_migrations (version) VALUES (5)'))
        if not connection.execute(text('SELECT version FROM schema_migrations WHERE version = 6')).first():
            connection.execute(text('INSERT INTO schema_migrations (version) VALUES (6)'))
        if 'reply_to_id' not in {c['name'] for c in inspect(connection).get_columns('messages')}:
            connection.execute(text('ALTER TABLE messages ADD COLUMN reply_to_id VARCHAR(64)'))
        if not connection.execute(text('SELECT version FROM schema_migrations WHERE version = 7')).first():
            connection.execute(text('INSERT INTO schema_migrations (version) VALUES (7)'))
        # Performance-only indexes also apply to existing v7 stores; no data-format change.
        for table in (support.Message.__table__, support.Ticket.__table__):
            for index in table.indexes:
                index.create(connection, checkfirst=True)

        if not connection.execute(text("SELECT version FROM schema_migrations WHERE version = 8")).first():
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES (8)"))

        if 'email_verified' not in {c['name'] for c in inspect(connection).get_columns('customer_accounts')}:
            connection.execute(text('ALTER TABLE customer_accounts ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT FALSE'))
        if not connection.execute(text("SELECT version FROM schema_migrations WHERE version = 9")).first():
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES (9)"))
        if not connection.execute(text("SELECT version FROM schema_migrations WHERE version = 10")).first():
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES (10)"))
        if engine.dialect.name == "sqlite" and not connection.execute(
                text("SELECT version FROM schema_migrations WHERE version = 11")).first():
            # Existing SQLite tables cannot receive CHECK/FK clauses through ALTER TABLE.
            # These triggers enforce the same invariants without rewriting user data.
            checks = [
                ("conversations", "status", "open", "handoff_requested", "assigned", "resolved", "closed"),
                ("conversations", "priority", "low", "normal", "high", "urgent"),
                ("tickets", "status", "open", "assigned", "resolved", "closed"),
                ("tickets", "priority", "low", "normal", "high", "urgent"),
                ("orders", "status", "processing", "paid", "shipping", "shipped", "delivered", "cancelled"),
                ("telegram_updates", "state", "pending", "processing", "done"),
                ("telegram_deliveries", "state", "pending", "sending", "sent", "failed", "uncertain", "skipped"),
                ("knowledge_documents", "status", "uploaded", "processing", "indexed", "failed", "deleting"),
            ]
            columns_by_table = {
                table: {column["name"] for column in inspect(connection).get_columns(table)}
                for table in {item[0] for item in checks}
            }
            checks = [item for item in checks if item[1] in columns_by_table[item[0]]]
            for table, column, *values in checks:
                quoted = ", ".join(f"'{value}'" for value in values)
                invalid = connection.execute(text(
                    f"SELECT COUNT(*) FROM {table} WHERE {column} NOT IN ({quoted})"
                )).scalar_one()
                if invalid:
                    raise ValueError(f"Cannot enforce {table}.{column}: {invalid} invalid row(s)")
            invalid_last_messages = connection.execute(text("""
                SELECT COUNT(*) FROM conversations AS c
                WHERE c.last_customer_message_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM messages AS m WHERE m.id = c.last_customer_message_id
                  )
            """)).scalar_one()
            if invalid_last_messages:
                raise ValueError(
                    "Cannot enforce conversations.last_customer_message_id: "
                    f"{invalid_last_messages} invalid row(s)")
            for table, column, *values in checks:
                quoted = ", ".join(f"'{value}'" for value in values)
                trigger_name = f"ck_{table}_{column}_allowed"
                connection.execute(text(f"""
                    CREATE TRIGGER IF NOT EXISTS {trigger_name}_insert
                    BEFORE INSERT ON {table}
                    WHEN NEW.{column} NOT IN ({quoted})
                    BEGIN SELECT RAISE(ABORT, 'invalid {table}.{column}'); END
                """))
                connection.execute(text(f"""
                    CREATE TRIGGER IF NOT EXISTS {trigger_name}_update
                    BEFORE UPDATE OF {column} ON {table}
                    WHEN NEW.{column} NOT IN ({quoted})
                    BEGIN SELECT RAISE(ABORT, 'invalid {table}.{column}'); END
                """))
            connection.execute(text("""
                CREATE TRIGGER IF NOT EXISTS fk_conversations_last_customer_message_insert
                BEFORE INSERT ON conversations
                WHEN NEW.last_customer_message_id IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM messages WHERE id = NEW.last_customer_message_id
                )
                BEGIN SELECT RAISE(ABORT, 'invalid conversations.last_customer_message_id'); END
            """))
            connection.execute(text("""
                CREATE TRIGGER IF NOT EXISTS fk_conversations_last_customer_message_update
                BEFORE UPDATE OF last_customer_message_id ON conversations
                WHEN NEW.last_customer_message_id IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM messages WHERE id = NEW.last_customer_message_id
                )
                BEGIN SELECT RAISE(ABORT, 'invalid conversations.last_customer_message_id'); END
            """))
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES (11)"))
