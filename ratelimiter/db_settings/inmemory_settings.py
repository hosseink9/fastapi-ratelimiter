from .base_limit_storage import RateLimitStorage
import asyncio

# In-memory storage
class InMemoryStorage(RateLimitStorage):
    def __init__(self):
        self.store = {}

    async def get_tokens(self, key: str):
        return self.store.get(f"{key}:tokens", None)

    async def set_tokens(self, key: str, tokens: float, ttl: int):
        self.store[f"{key}:tokens"] = tokens

    async def get_last_request_time(self, key: str):
        return self.store.get(f"{key}:last_request", None)

    async def set_last_request_time(self, key: str, last_request: float):
        self.store[f"{key}:last_request"] = last_request

    async def ban_client(self, key: str, ban_until: float):
        self.store[f"{key}:banned_until"] = ban_until

    async def is_banned(self, key: str, current_time: float) -> bool:
        banned_until = self.store.get(f"{key}:banned_until")
        return banned_until and float(banned_until) > current_time