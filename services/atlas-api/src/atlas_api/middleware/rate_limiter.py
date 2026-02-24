"""
Rate limiter por IP usando Starlette BaseHTTPMiddleware.
Protege endpoints /atlas/evaluate contra abuso.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class SmartRateLimiter(BaseHTTPMiddleware):
    """
    Middleware de rate limiting por IP.

    Configurável via ``max_rpm`` (requests por minuto).
    Aplica-se apenas a rotas que começam com ``/atlas/``.
    """

    def __init__(self, app: Any, *, max_rpm: int = 60):
        super().__init__(app)
        self.max_rpm = max_rpm
        # ip -> list of timestamps (epoch floats)
        self._hits: Dict[str, List[float]] = defaultdict(list)

    # ---- helpers ----
    def _prune(self, ip: str, now: float) -> None:
        """Remove registros com mais de 60 s."""
        cutoff = now - 60.0
        bucket = self._hits[ip]
        # find first index >= cutoff
        i = 0
        while i < len(bucket) and bucket[i] < cutoff:
            i += 1
        if i:
            self._hits[ip] = bucket[i:]

    def _is_limited(self, ip: str) -> bool:
        now = time.monotonic()
        self._prune(ip, now)
        self._hits[ip].append(now)
        return len(self._hits[ip]) > self.max_rpm

    # ---- middleware entry point ----
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        # Only rate-limit ATLAS evaluation endpoints
        if request.url.path.startswith("/atlas/"):
            client_ip = request.client.host if request.client else "unknown"
            if self._is_limited(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": {
                            "error": "RATE_LIMIT_EXCEEDED",
                            "message": f"Máximo de {self.max_rpm} requisições por minuto excedido",
                            "retry_after": 60,
                        }
                    },
                )
        return await call_next(request)
