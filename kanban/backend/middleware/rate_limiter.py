from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict
import time
import threading

# Thread-safe in-memory store (for single-worker dev/prod)
_request_logs = defaultdict(list)
_lock = threading.Lock()

DAILY_LIMIT = 500
WINDOW_SECONDS = 86400  # 24 hours

def _get_client_identifier(request: Request) -> str:
    # Prefer session ID from header, fallback to IP
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        return f"session:{session_id}"
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"

def _is_rate_limited(identifier: str) -> bool:
    now = time.time()
    with _lock:
        # Clean expired requests
        _request_logs[identifier] = [
            ts for ts in _request_logs[identifier] if now - ts < WINDOW_SECONDS
        ]
        return len(_request_logs[identifier]) >= DAILY_LIMIT

def _record_request(identifier: str):
    with _lock:
        _request_logs[identifier].append(time.time())

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only apply to chat endpoints
        if request.url.path.startswith("/api/chat"):
            identifier = _get_client_identifier(request)
            if _is_rate_limited(identifier):
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": f"Limit: {DAILY_LIMIT} requests per day",
                        "reset": "in 24 hours"
                    }
                )
            _record_request(identifier)

        response = await call_next(request)
        return response