import time
import asyncio
from math import floor

import aiohttp


class RateLimiter:
    def __init__(self, client, max_tokens=None, rate=None):
        self.client = client

        if max_tokens is None:
            self.max_tokens = 30
        else:
            self.max_tokens = max_tokens

        self.n_tokens = self.max_tokens

        if rate is None:
            self.rate = 0.8*(self.max_tokens/1)
        else:
            self.rate = rate

        self.updated_at = time.monotonic()

    async def get(self, *args, **kwargs):
        await self.wait_for_token()
        return await self.client.get(*args, **kwargs)

    async def wait_for_token(self):
        while self.n_tokens < 1:
            self.add_new_token()
            await asyncio.sleep(0.1)

        self.n_tokens -= 1

    def add_new_token(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at

        new_tokens = floor(time_since_update * self.rate)
        if self.n_tokens + new_tokens > 0:
            self.n_tokens = min(self.n_tokens + new_tokens, self.max_tokens)
            self.updated_at = now