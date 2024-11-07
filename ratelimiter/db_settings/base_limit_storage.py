import asyncio

class RateLimitStorage:
    async def get_tokens(self, key: str):
        raise NotImplementedError

    async def set_tokens(self, key: str, tokens: float, ttl: int):
        raise NotImplementedError

    async def get_last_request_time(self, key: str):
        raise NotImplementedError

    async def set_last_request_time(self, key: str, last_request: float):
        raise NotImplementedError

    async def ban_client(self, key: str, ban_until: float):
        raise NotImplementedError

    async def is_banned(self, key: str, current_time: float) -> bool:
        raise NotImplementedError
