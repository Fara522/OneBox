import aiomysql
import database.db as _db


def pool():
    return _db.pool


class OrderModel:

    @staticmethod
    async def create(customer_id: int, product_name: str, quantity: int, comment: str | None = None) -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO orders (customer_id, product_name, quantity, comment) VALUES (%s,%s,%s,%s)",
                    (customer_id, product_name, quantity, comment),
                )
                return cur.lastrowid

    @staticmethod
    async def get_by_id(order_id: int) -> dict | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """SELECT o.*, u.full_name as customer_name, u.telegram_id as customer_tg
                       FROM orders o JOIN users u ON o.customer_id = u.id
                       WHERE o.id = %s""",
                    (order_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def get_pending() -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """SELECT o.*, u.full_name as customer_name
                       FROM orders o JOIN users u ON o.customer_id = u.id
                       WHERE o.status IN ('pending','next_stage')
                       ORDER BY o.created_at ASC"""
                )
                return await cur.fetchall()

    @staticmethod
    async def get_by_customer(customer_id: int) -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM orders WHERE customer_id=%s ORDER BY created_at DESC LIMIT 20",
                    (customer_id,),
                )
                return await cur.fetchall()

    @staticmethod
    async def set_status(order_id: int, status: str):
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                if status == "completed":
                    await cur.execute(
                        "UPDATE orders SET status=%s, completed_at=NOW() WHERE id=%s",
                        (status, order_id),
                    )
                else:
                    await cur.execute(
                        "UPDATE orders SET status=%s WHERE id=%s",
                        (status, order_id),
                    )

    @staticmethod
    async def get_stage_count(order_id: int) -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) FROM order_stages WHERE order_id=%s",
                    (order_id,),
                )
                row = await cur.fetchone()
                return row[0] if row else 0

    @staticmethod
    async def create_stage(order_id: int, worker_id: int, machine_id: int, stage_number: int, helper_name: str | None = None) -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """INSERT INTO order_stages (order_id, worker_id, machine_id, stage_number, helper_name, start_time)
                       VALUES (%s,%s,%s,%s,%s,NOW())""",
                    (order_id, worker_id, machine_id, stage_number, helper_name),
                )
                return cur.lastrowid

    @staticmethod
    async def get_active_stage(worker_id: int) -> dict | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """SELECT s.*, o.product_name, o.quantity, o.comment, o.customer_id,
                              m.name as machine_name, u.full_name as customer_name,
                              u.telegram_id as customer_tg
                       FROM order_stages s
                       JOIN orders o ON s.order_id = o.id
                       JOIN machines m ON s.machine_id = m.id
                       JOIN users u ON o.customer_id = u.id
                       WHERE s.worker_id=%s AND s.status='in_progress'
                       ORDER BY s.start_time DESC LIMIT 1""",
                    (worker_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def complete_stage(stage_id: int) -> dict | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "UPDATE order_stages SET status='completed', end_time=NOW() WHERE id=%s",
                    (stage_id,),
                )
                await cur.execute(
                    """SELECT s.*, o.product_name, o.quantity, o.id as order_id,
                              o.customer_id, m.name as machine_name, u.full_name as worker_name,
                              cu.full_name as customer_name, cu.telegram_id as customer_tg
                       FROM order_stages s
                       JOIN orders o ON s.order_id = o.id
                       JOIN machines m ON s.machine_id = m.id
                       JOIN users u ON s.worker_id = u.id
                       JOIN users cu ON o.customer_id = cu.id
                       WHERE s.id=%s""",
                    (stage_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def pass_stage(stage_id: int) -> dict | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "UPDATE order_stages SET status='passed', end_time=NOW() WHERE id=%s",
                    (stage_id,),
                )
                await cur.execute(
                    "SELECT order_id FROM order_stages WHERE id=%s",
                    (stage_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def get_all(limit: int = 20, offset: int = 0) -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """SELECT o.*, u.full_name as customer_name
                       FROM orders o JOIN users u ON o.customer_id = u.id
                       ORDER BY o.created_at DESC LIMIT %s OFFSET %s""",
                    (limit, offset),
                )
                return await cur.fetchall()

    @staticmethod
    async def count_all() -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM orders")
                row = await cur.fetchone()
                return row[0] if row else 0
