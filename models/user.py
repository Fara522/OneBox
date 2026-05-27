import aiomysql
import database.db as _db


def pool():
    return _db.pool


class UserModel:

    @staticmethod
    async def get_by_telegram_id(telegram_id: int) -> dict | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM users WHERE telegram_id = %s AND is_active = 1",
                    (telegram_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def get_by_login(login: str) -> dict | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM users WHERE login = %s AND is_active = 1",
                    (login,),
                )
                return await cur.fetchone()

    @staticmethod
    async def get_by_id(user_id: int) -> dict | None:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM users WHERE id = %s",
                    (user_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def link_telegram(user_id: int, telegram_id: int, username: str | None):
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET telegram_id = %s, username = %s WHERE id = %s",
                    (telegram_id, username, user_id),
                )

    @staticmethod
    async def create_worker(full_name: str, age: int | None = None) -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (full_name, role, age) VALUES (%s, 'worker', %s)",
                    (full_name, age),
                )
                return cur.lastrowid

    @staticmethod
    async def get_workers_with_machine() -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT u.id, u.full_name, u.age, u.telegram_id,
                           m.name as machine_name
                    FROM users u
                    LEFT JOIN assignments a ON a.worker_id = u.id AND a.is_active = 1
                    LEFT JOIN machines m ON a.machine_id = m.id
                    WHERE u.role = 'worker' AND u.is_active = 1
                    ORDER BY u.full_name
                """)
                return await cur.fetchall()

    @staticmethod
    async def create_staff(full_name: str, role: str, login: str, password_hash: str) -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (full_name, role, login, password_hash) VALUES (%s, %s, %s, %s)",
                    (full_name, role, login, password_hash),
                )
                return cur.lastrowid

    @staticmethod
    async def get_all_by_role(role: str) -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM users WHERE role = %s AND is_active = 1 ORDER BY full_name",
                    (role,),
                )
                return await cur.fetchall()

    @staticmethod
    async def get_unlinked_by_role(role: str) -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM users WHERE role = %s AND is_active = 1 AND telegram_id IS NULL ORDER BY full_name",
                    (role,),
                )
                return await cur.fetchall()

    @staticmethod
    async def get_unlinked_workers() -> list[dict]:
        return await UserModel.get_unlinked_by_role("worker")

    @staticmethod
    async def get_all_bosses_with_telegram() -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM users WHERE role = 'boss' AND is_active = 1 AND telegram_id IS NOT NULL"
                )
                return await cur.fetchall()

    @staticmethod
    async def get_all_admins_with_telegram() -> list[dict]:
        async with pool().acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM users WHERE role = 'admin' AND is_active = 1 AND telegram_id IS NOT NULL"
                )
                return await cur.fetchall()

    @staticmethod
    async def deactivate(user_id: int):
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET is_active = 0 WHERE id = %s",
                    (user_id,),
                )

    @staticmethod
    async def update_full_name(user_id: int, full_name: str):
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET full_name = %s WHERE id = %s",
                    (full_name, user_id),
                )

    @staticmethod
    async def update_password(user_id: int, password_hash: str):
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (password_hash, user_id),
                )

    @staticmethod
    async def logout(telegram_id: int):
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET telegram_id = NULL WHERE telegram_id = %s",
                    (telegram_id,),
                )

    @staticmethod
    async def create_customer(full_name: str) -> int:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (full_name, role) VALUES (%s, 'customer')",
                    (full_name,),
                )
                return cur.lastrowid

    @staticmethod
    async def login_exists(login: str) -> bool:
        async with pool().acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id FROM users WHERE login = %s",
                    (login,),
                )
                return await cur.fetchone() is not None
