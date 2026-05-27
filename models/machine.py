import aiomysql
import database.db as _db


def pool():
    return _db.pool


class MachineModel:

    @staticmethod
    async def get_all_active() -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM machines WHERE is_active = 1 ORDER BY name"
                )
                return await cur.fetchall()

    @staticmethod
    async def get_by_id(machine_id: int) -> dict | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM machines WHERE id = %s",
                    (machine_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def create(name: str, description: str | None = None) -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO machines (name, description) VALUES (%s, %s)",
                    (name, description),
                )
                return cur.lastrowid

    @staticmethod
    async def update_name(machine_id: int, name: str):
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE machines SET name = %s WHERE id = %s",
                    (name, machine_id),
                )

    @staticmethod
    async def deactivate(machine_id: int):
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE machines SET is_active = 0 WHERE id = %s",
                    (machine_id,),
                )
