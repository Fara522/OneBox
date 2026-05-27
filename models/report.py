import aiomysql
from datetime import datetime, timedelta
import database.db as _db


def pool():
    return _db.pool


class ReportModel:

    @staticmethod
    async def create(
        worker_id: int,
        machine_id: int,
        product_name: str,
        quantity: int,
        start_time: datetime,
        assistant_name: str | None = None,
    ) -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """INSERT INTO reports
                       (worker_id, assistant_name, machine_id, product_name, quantity, start_time)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (worker_id, assistant_name, machine_id, product_name, quantity, start_time),
                )
                return cur.lastrowid

    @staticmethod
    async def complete(report_id: int, end_time: datetime) -> int | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT start_time FROM reports WHERE id = %s",
                    (report_id,),
                )
                row = await cur.fetchone()
                if not row:
                    return None
                duration = max(1, int((end_time - row["start_time"]).total_seconds() / 60))
                await cur.execute(
                    """UPDATE reports
                       SET end_time = %s, duration_minutes = %s, status = 'completed'
                       WHERE id = %s""",
                    (end_time, duration, report_id),
                )
                return duration

    @staticmethod
    async def get_by_id(report_id: int) -> dict | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """SELECT r.*, u.full_name as worker_name, m.name as machine_name
                       FROM reports r
                       JOIN users u ON r.worker_id = u.id
                       JOIN machines m ON r.machine_id = m.id
                       WHERE r.id = %s""",
                    (report_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def get_active_for_worker(worker_id: int) -> dict | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """SELECT r.*, m.name as machine_name
                       FROM reports r
                       JOIN machines m ON r.machine_id = m.id
                       WHERE r.worker_id = %s AND r.status = 'in_progress'
                       ORDER BY r.created_at DESC LIMIT 1""",
                    (worker_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def get_all(limit: int = 10, offset: int = 0) -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """SELECT r.*, u.full_name as worker_name, m.name as machine_name
                       FROM reports r
                       JOIN users u ON r.worker_id = u.id
                       JOIN machines m ON r.machine_id = m.id
                       ORDER BY r.created_at DESC
                       LIMIT %s OFFSET %s""",
                    (limit, offset),
                )
                return await cur.fetchall()

    @staticmethod
    async def count_all() -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM reports")
                row = await cur.fetchone()
                return row[0] if row else 0

    @staticmethod
    async def get_stats(period: str = "daily") -> dict:
        now = datetime.now()
        if period == "daily":
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)
            label = "Bugungi"
        elif period == "weekly":
            since = now - timedelta(days=7)
            label = "Haftalik"
        else:
            since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            label = "Oylik"

        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """SELECT COUNT(*) as total_reports,
                              COALESCE(SUM(quantity), 0) as total_quantity,
                              COALESCE(AVG(duration_minutes), 0) as avg_duration,
                              COALESCE(SUM(duration_minutes), 0) as total_minutes
                       FROM reports
                       WHERE status = 'completed' AND created_at >= %s""",
                    (since,),
                )
                summary = await cur.fetchone()

                await cur.execute(
                    """SELECT u.full_name, COUNT(*) as cnt, COALESCE(SUM(r.quantity), 0) as qty
                       FROM reports r
                       JOIN users u ON r.worker_id = u.id
                       WHERE r.status = 'completed' AND r.created_at >= %s
                       GROUP BY r.worker_id ORDER BY qty DESC""",
                    (since,),
                )
                by_worker = await cur.fetchall()

                await cur.execute(
                    """SELECT m.name, COUNT(*) as cnt, COALESCE(SUM(r.quantity), 0) as qty
                       FROM reports r
                       JOIN machines m ON r.machine_id = m.id
                       WHERE r.status = 'completed' AND r.created_at >= %s
                       GROUP BY r.machine_id ORDER BY qty DESC""",
                    (since,),
                )
                by_machine = await cur.fetchall()

        return {
            "label": label,
            "summary": summary,
            "by_worker": by_worker,
            "by_machine": by_machine,
            "since": since,
        }
