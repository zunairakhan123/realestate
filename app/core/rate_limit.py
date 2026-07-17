import time
from fastapi import Request
from collections import defaultdict
from app.core.exceptions import RateLimitExceededError

# In-memory store: { "user_or_ip_key": [timestamp1, timestamp2, ...] }
# Note: In a real multi-server production app, this would be backed by Redis.
_rate_limit_store = defaultdict(list)

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request):
        # 1. Identify the caller (Fallback to IP if token is missing)
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Key by token (identifies the specific user)
            client_key = auth_header.split(" ")[-1]
        else:
            # Key by IP (identifies unauthenticated clients)
            client_key = request.client.host
        
        now = time.time()
        
        # 2. Sliding Window: Remove timestamps older than the time window
        _rate_limit_store[client_key] = [
            t for t in _rate_limit_store[client_key] 
            if now - t < self.window_seconds
        ]
        
        # 3. Check if they hit the limit
        if len(_rate_limit_store[client_key]) >= self.max_requests:
            raise RateLimitExceededError(
                f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds."
            )
        
        # 4. Record the new request
        _rate_limit_store[client_key].append(now)