from sqlalchemy import Connection, text
from sqlalchemy.ext.asyncio import AsyncConnection


def insert_rbac_seed_data_sync(conn: Connection) -> None:
    conn.execute(
        text(
            """
            INSERT INTO roles (id, name, description, is_system, created_at, updated_at)
            VALUES
                (1, 'admin', 'System administrator role', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 'user', 'Default user role', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
            """
        )
    )


async def insert_rbac_seed_data_async(conn: AsyncConnection) -> None:
    await conn.execute(
        text(
            """
            INSERT INTO roles (id, name, description, is_system, created_at, updated_at)
            VALUES
                (1, 'admin', 'System administrator role', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 'user', 'Default user role', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
            """
        )
    )
    await conn.commit()
