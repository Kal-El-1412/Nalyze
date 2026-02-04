import time
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import config

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = str(uuid.uuid4())

        request.state.correlation_id = correlation_id

        if request.method == "POST" and request.url.path == "/chat":
            try:
                original_receive = request._receive
                body_bytes = await request.body()
                import json
                body_data = json.loads(body_bytes) if body_bytes else {}
                conversation_id = body_data.get("conversationId")
                if conversation_id:
                    correlation_id = conversation_id
                    request.state.correlation_id = correlation_id

                has_replayed = False
                async def receive():
                    nonlocal has_replayed
                    if not has_replayed:
                        has_replayed = True
                        return {"type": "http.request", "body": body_bytes, "more_body": False}
                    return await original_receive()

                request._receive = receive
            except Exception as e:
                logger.debug(f"Could not extract conversationId: {e}")

        start_time = time.time()

        logger.info(
            f"[{correlation_id}] {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                f"[{correlation_id}] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration_ms:.2f}ms"
            )

            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[{correlation_id}] {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration_ms:.2f}ms",
                exc_info=True
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 60
        self.last_cleanup = time.time()

    def _cleanup_old_requests(self):
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            cutoff_time = datetime.now() - timedelta(minutes=2)
            for client_ip in list(self.requests.keys()):
                self.requests[client_ip] = [
                    req_time for req_time in self.requests[client_ip]
                    if req_time > cutoff_time
                ]
                if not self.requests[client_ip]:
                    del self.requests[client_ip]
            self.last_cleanup = current_time

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        self._cleanup_old_requests()

        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        recent_requests = [
            req_time for req_time in self.requests[client_ip]
            if req_time > one_minute_ago
        ]

        rate_limit = config.rate_limit_requests_per_minute

        if len(recent_requests) >= rate_limit:
            logger.warning(
                f"Rate limit exceeded for client {client_ip}: "
                f"{len(recent_requests)} requests in last minute"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {rate_limit} requests per minute."
            )

        self.requests[client_ip].append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(rate_limit - len(recent_requests) - 1)

        return response
