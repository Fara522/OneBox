import aiomysql
import database.db as _db


def pool():
    return _db.pool


class AssignmentModel:

    @staticmethod
    async def create(machine_id: int, worker_id: int) -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE assignments SET is_active = 0 WHERE worker_id = %s",
                    (worker_id,),
                )
                await cur.execute(
                    "INSERT INTO assignments (machine_id, worker_id) VALUES (%s, %s)",
                    (machine_id, worker_id),
                )
                return cur.lastrowid

    @staticmethod
    async def get_all_active() -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT a.id, a.assigned_at,
                           u.id as worker_id, u.full_name as worker_name,
                           m.id as machine_id, m.name as machine_name
                    FROM assignments a
                    JOIN users u ON a.worker_id = u.id
                    JOIN machines m ON a.machine_id = m.id
                    WHERE a.is_active = 1 AND u.is_active = 1 AND m.is_active = 1
                    ORDER BY m.name, u.full_name
                """)
                return await cur.fetchall()

    @staticmethod
    async def remove_worker(worker_id: int):
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE assignments SET is_active = 0 WHERE worker_id = %s",
                    (worker_id,),
                )
