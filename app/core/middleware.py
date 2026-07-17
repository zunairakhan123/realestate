import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import logger, request_id_var

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Extract existing ID from client, or generate a new one
        req_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
        
        # 2. Bind the ID to this specific async task
        token = request_id_var.set(req_id)
        
        # High-precision timer
        start_time = time.perf_counter()
        
        try:
            # 3. Pass request down the chain
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            # 4. Calculate duration and log the JSON
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": round(duration_ms, 2)
                }
            )
            
            # Clean up memory
            request_id_var.reset(token)

        # 5. Attach ID to the outgoing response headers
        response.headers["X-Request-ID"] = req_id
        return response