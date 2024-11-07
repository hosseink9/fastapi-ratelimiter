import asyncpg
from time import time


class SQLStorage:
    def __init__(self, dsn: str, table_name: str="rate_limit"):
        """
        Initialize connection to PostgreSQL.
        dsn: Database connection string (e.g., "postgresql://user:password@localhost/dbname")
        """
        self.dsn = dsn
        self.table_name = table_name

    async def connect(self):
        """Establishes a connection pool to the PostgreSQL database."""
        self.pool = await asyncpg.create_pool(dsn=self.dsn)
        await self._create_table()

    async def _create_table(self):
        """Creates the rate_limit table if it does not exist."""
        async with self.pool.acquire() as conn:
            await conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    key TEXT NOT NULL,
                    tokens TEXT,
                    last_request REAL,
                    banned_until REAL
                )
            ''')

    async def get_tokens(self, key: str):
        """Retrieve the token count for a specific key."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT tokens FROM rate_limit WHERE key = $1', key)
            return row['tokens'] if row else None

    async def set_tokens(self, key: str, tokens: float, ttl: int):
        """Set the token count and ensure the record expires."""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO rate_limit (key, tokens, last_request) 
                VALUES ($1, $2, $3)
                ON CONFLICT (key) 
                DO UPDATE SET tokens = $2, last_request = $3
            ''', key, tokens, time())

    async def get_last_request_time(self, key: str):
        """Retrieve the last request time for a specific key."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT last_request FROM rate_limit WHERE key = $1', key)
            return row['last_request'] if row else None

    async def set_last_request_time(self, key: str, last_request: float):
        """Set the last request time for a specific key."""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO rate_limit (key, last_request) 
                VALUES ($1, $2)
                ON CONFLICT (key) 
                DO UPDATE SET last_request = $2
            ''', key, last_request)

    async def ban_client(self, key: str, ban_until: float):
        """Ban a client by setting a banned_until timestamp."""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO rate_limit (key, banned_until) 
                VALUES ($1, $2)
                ON CONFLICT (key) 
                DO UPDATE SET banned_until = $2
            ''', key, ban_until)

    async def is_banned(self, key: str, current_time: float) -> bool:
        """Check if a client is banned."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT banned_until FROM rate_limit WHERE key = $1', key)
            return row and row['banned_until'] and float(row['banned_until']) > current_time

