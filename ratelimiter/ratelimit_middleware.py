from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import asyncio
from time import time

app = FastAPI()

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, request_limit=10, ban_duration=600, refill_rate=1, redis_url='redis://localhost:6379/0'):
        super().__init__(app)
        self.request_limit = request_limit
        self.ban_duration = ban_duration
        self.refill_rate = refill_rate
        
        self.redis = redis.from_url(redis_url)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time()

        # Key for the current client's rate limit
        key = f"rate_limit:{client_ip}"

        # Check if the IP is banned
        banned_until = await self.redis.get(f"{key}:banned_until")
        if banned_until and float(banned_until) > current_time:
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests, IP is banned for {self.ban_duration // 60} minutes."
            )

        # Retrieve tokens and last request time
        tokens = await self.redis.get(f"{key}:tokens")
        last_request = await self.redis.get(f"{key}:last_request")

        if tokens is None:
            tokens = self.request_limit
            last_request = current_time
            await self.redis.set(key + ":tokens", tokens)
            await self.redis.set(key + ":last_request", last_request)
            await self.redis.expire(key + ":tokens", self.ban_duration + 1)  # Expire in case of inactivity

        tokens = float(tokens)
        last_request = float(last_request)

        elapsed_time = current_time - last_request
        new_tokens = min(self.request_limit, tokens + elapsed_time * self.refill_rate)

        if new_tokens < 1:
            # Ban the IP
            await self.redis.set(f"{key}:banned_until", current_time + self.ban_duration)
            await self.redis.set(key + ":tokens", 0)  # Reset tokens on ban
            await self.redis.expire(f"{key}:banned_until", self.ban_duration)
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests, IP is banned for {self.ban_duration // 60} minutes."
            )

        # Update Redis with the new token count and last request time
        await self.redis.set(key + ":tokens", new_tokens - 1)
        await self.redis.set(key + ":last_request", current_time)

        response = await call_next(request)
        return response
