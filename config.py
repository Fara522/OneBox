import os
import aiomysql

pool = None

async def create_pool():
    global pool

    pool = await aiomysql.create_pool(
        host=os.getenv("MYSQLHOST"),
        port=int(os.getenv("MYSQLPORT")),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        db=os.getenv("MYSQLDATABASE"),
    )
# import os
# from dotenv import load_dotenv

# load_dotenv()

# BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# DB_HOST: str = os.getenv("DB_HOST", "localhost")
# DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
# DB_USER: str = os.getenv("DB_USER", "root")
# DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
# DB_NAME: str = os.getenv("DB_NAME", "onebox_bot")
