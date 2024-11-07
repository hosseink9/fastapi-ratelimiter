from .base_limit_storage import RateLimitStorage
import asyncio
import redis
from time import time


class RedisStorage(RateLimitStorage):
    def __init__(self, redis_url='redis://localhost:6379/0', key_prefix="rate_limit"):
        self.redis = redis.from_url(redis_url)
        self.key_prefix = key_prefix

    def _make_key(self, key_suffix: str) -> str:
        """Helper method to create a namespaced key."""
        return f"{self.key_prefix}:{key_suffix}"

    async def get_tokens(self, key: str):
        return await self.redis.get(self._make_key(f"{key}:tokens"))

    async def set_tokens(self, key: str, tokens: float, ttl: int):
        await self.redis.set(self._make_key(f"{key}:tokens"), tokens)
        await self.redis.expire(self._make_key(f"{key}:tokens"), ttl)

    async def get_last_request_time(self, key: str):
        return await self.redis.get(self._make_key(f"{key}:last_request"))

    async def set_last_request_time(self, key: str, last_request: float):
        await self.redis.set(self._make_key(f"{key}:last_request"), last_request)

    async def ban_client(self, key: str, ban_until: float):
        await self.redis.set(self._make_key(f"{key}:banned_until"), ban_until)
        await self.redis.expire(self._make_key(f"{key}:banned_until"), int(ban_until - time()))

    async def is_banned(self, key: str, current_time: float) -> bool:
        banned_until = await self.redis.get(self._make_key(f"{key}:banned_until"))
        return banned_until and float(banned_until) > current_time
