from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
from db_settings.inmemory_settings import InMemoryStorage
from db_settings.redis_settings import RedisStorage
from db_settings.sql_settings import SQLStorage 
from time import time

app = FastAPI()


# Middleware with dynamic storage selection
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, storage_backend='memory', request_limit=10, ban_duration=600, refill_rate=1, redis_url=None, dsn=None, table_name="rate_limit"):
        super().__init__(app)
        self.request_limit = request_limit
        self.ban_duration = ban_duration
        self.refill_rate = refill_rate

        if storage_backend == 'redis':
            self.storage = RedisStorage(redis_url, table_name)
        elif storage_backend == 'sql':
            self.storage = SQLStorage(dsn, table_name)
        else:
            self.storage = InMemoryStorage()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time()

        key = f"rate_limit:{client_ip}"

        # Check if the IP is banned
        if await self.storage.is_banned(key, current_time):
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests, IP is banned for {self.ban_duration // 60} minutes."
            )

        tokens = await self.storage.get_tokens(key) or self.request_limit
        last_request = await self.storage.get_last_request_time(key) or current_time

        elapsed_time = current_time - last_request
        new_tokens = min(self.request_limit, tokens + elapsed_time * self.refill_rate)

        if new_tokens < 1:
            await self.storage.ban_client(key, current_time + self.ban_duration)
            await self.storage.set_tokens(key, 0, self.ban_duration)
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests, IP is banned for {self.ban_duration // 60} minutes."
            )

        await self.storage.set_tokens(key, new_tokens - 1, self.ban_duration)
        await self.storage.set_last_request_time(key, current_time)

        return await call_next(request)

app.add_middleware(RateLimitMiddleware, storage_backend='redis')
