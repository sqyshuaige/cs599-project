"""
生产级可观测性中间件
- 结构化请求日志
- 请求响应时间统计
- Token 消耗估算
- 健康检查端点
"""
import time
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import json

# 配置 loguru
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logger.remove()
logger.add(
    os.path.join(LOG_DIR, "oa_server_{time:YYYY-MM-DD}.log"),
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[request_id]} | {message}",
    encoding="utf-8",
)
logger.add(sys.stdout, level="INFO",
           format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[request_id]}</cyan> | <level>{message}</level>")


# Token 估算器
class TokenEstimator:
    """基于经验公式估算 Token 消耗（中文约 1.5 字符/token）"""

    @staticmethod
    def estimate_input(text: str) -> int:
        return max(1, len(text) // 2)

    @staticmethod
    def estimate_output(text: str) -> int:
        return max(1, len(text) // 2)

    @staticmethod
    def estimate_cost(input_tokens: int, output_tokens: int) -> float:
        # DeepSeek Chat: 输入 1元/百万token, 输出 2元/百万token
        return (input_tokens / 1_000_000) * 1.0 + (output_tokens / 1_000_000) * 2.0


# 统计计数器
class MetricsCollector:
    def __init__(self):
        self.total_requests = 0
        self.total_errors = 0
        self.total_llm_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.start_time = time.time()

    def record_request(self, status_code: int):
        self.total_requests += 1
        if status_code >= 400:
            self.total_errors += 1

    def record_llm_call(self, input_tokens: int, output_tokens: int):
        self.total_llm_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += TokenEstimator.estimate_cost(input_tokens, output_tokens)

    def get_summary(self) -> dict:
        uptime = time.time() - self.start_time
        return {
            "uptime_seconds": round(uptime, 1),
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": f"{self.total_errors / max(1, self.total_requests) * 100:.2f}%",
            "total_llm_calls": self.total_llm_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_rmb": f"¥{self.total_cost:.4f}",
        }


metrics = MetricsCollector()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """请求日志 + 计时 + 统计中间件"""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # 结构化日志上下文
        with logger.contextualize(request_id=request_id):
            logger.info(f"{request.method} {request.url.path} | client={request.client.host}")

            try:
                response: Response = await call_next(request)
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_request(response.status_code)

                logger.info(
                    f"{response.status_code} | {duration_ms:.0f}ms | "
                    f"{request.method} {request.url.path}"
                )
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time-Ms"] = str(round(duration_ms))
                return response
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_request(500)
                logger.error(f"500 | {duration_ms:.0f}ms | {request.method} {request.url.path} | {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Internal Server Error", "request_id": request_id},
                )


def get_health_status() -> dict:
    """健康检查"""
    from app.database import SessionLocal
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute(db.bind.dialect.do_ping(None) if hasattr(db.bind.dialect, 'do_ping') else "SELECT 1")
        db.close()
    except Exception:
        db_status = "error"

    chroma_status = "ok"
    try:
        import chromadb
        from app.config import settings
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        client.heartbeat()
    except Exception:
        chroma_status = "disabled"

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "version": "2.0.0",
        "database": db_status,
        "chromadb": chroma_status,
        "metrics": metrics.get_summary(),
    }
