from datetime import UTC, datetime
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from alembic import context
from src.core.config import get_settings

from src.core.schemas import *  # noqa: F403

config = context.config

# Get settings before setting URL
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.db.url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def on_version_apply(connection: Connection, revision: str, direction: str) -> None:
    user = (
        context.get_x_argument("user") if hasattr(context, "get_x_argument") else None
    )

    sql = text(
        """
        INSERT INTO audit_logs (occurred_at, action, result, resource_type, resource_id, user_agent, ip, extra)
        VALUES (:occurred_at, :action, :result, :resource_type, :resource_id, :user_agent, :ip, :extra)
        """
    )

    occurred_at = datetime.now(UTC).isoformat()

    connection.execute(
        sql,
        {
            "occurred_at": occurred_at,
            "action": "migration",
            "result": "success",
            "resource_type": "migration",
            "resource_id": revision,
            "user_agent": "alembic",
            "ip": None,
            "extra": {
                "direction": direction,
                "executed_by": user,
                "revision": revision,
            },
        },
    )


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        on_version_apply=on_version_apply,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    import asyncio

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
