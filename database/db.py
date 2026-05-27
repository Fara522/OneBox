import aiomysql
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

pool: aiomysql.Pool = None


async def create_pool():
    global pool
    pool = await aiomysql.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        autocommit=True,
        charset="utf8mb4",
        minsize=1,
        maxsize=10,
    )


async def init_db():
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Migrate role column to include customer
            try:
                await cur.execute(
                    "ALTER TABLE users MODIFY COLUMN role ENUM('boss','admin','worker','customer') NOT NULL"
                )
            except Exception:
                pass
            # Migrate: add age column to workers
            try:
                await cur.execute("ALTER TABLE users ADD COLUMN age INT DEFAULT NULL")
            except Exception:
                pass
            # Migrate: add helper_name to order_stages
            try:
                await cur.execute("ALTER TABLE order_stages ADD COLUMN helper_name VARCHAR(200) DEFAULT NULL")
            except Exception:
                pass

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    telegram_id BIGINT UNIQUE DEFAULT NULL,
                    username VARCHAR(100) DEFAULT NULL,
                    full_name VARCHAR(200) NOT NULL,
                    age INT DEFAULT NULL,
                    role ENUM('boss','admin','worker','customer') NOT NULL,
                    login VARCHAR(100) UNIQUE DEFAULT NULL,
                    password_hash VARCHAR(255) DEFAULT NULL,
                    is_active TINYINT(1) DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS machines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT DEFAULT NULL,
                    is_active TINYINT(1) DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_id INT NOT NULL,
                    worker_id INT NOT NULL,
                    is_active TINYINT(1) DEFAULT 1,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE,
                    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    product_name VARCHAR(200) NOT NULL,
                    quantity INT NOT NULL,
                    comment TEXT DEFAULT NULL,
                    status ENUM('pending','in_progress','next_stage','completed','cancelled') DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME DEFAULT NULL,
                    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS order_stages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    worker_id INT NOT NULL,
                    machine_id INT NOT NULL,
                    stage_number INT NOT NULL DEFAULT 1,
                    helper_name VARCHAR(200) DEFAULT NULL,
                    status ENUM('in_progress','passed','completed') DEFAULT 'in_progress',
                    start_time DATETIME NOT NULL,
                    end_time DATETIME DEFAULT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            # Keep old reports table
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    worker_id INT NOT NULL,
                    assistant_name VARCHAR(200) DEFAULT NULL,
                    machine_id INT NOT NULL,
                    product_name VARCHAR(200) NOT NULL,
                    quantity INT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME DEFAULT NULL,
                    duration_minutes INT DEFAULT NULL,
                    status ENUM('in_progress','completed') DEFAULT 'in_progress',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
