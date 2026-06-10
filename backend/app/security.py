"""
生产级安全防护
- 速率限制 (IP级别 + 全局)
- 安全响应头
- 输入校验与消毒
- Prompt Injection 基础检测
"""
import re
import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RateLimiter:
    """基于滑动窗口的速率限制器"""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clients: dict[str, list[float]] = defaultdict(list)
        self._cleanup_time = time.time()

    def _cleanup(self):
        now = time.time()
        if now - self._cleanup_time < 60:
            return
        self._cleanup_time = now
        cutoff = now - self.window_seconds
        expired = [ip for ip, times in self._clients.items() if not any(t > cutoff for t in times)]
        for ip in expired:
            del self._clients[ip]

    def is_allowed(self, client_ip: str) -> bool:
        self._cleanup()
        now = time.time()
        cutoff = now - self.window_seconds
        self._clients[client_ip] = [t for t in self._clients[client_ip] if t > cutoff]
        self._clients[client_ip].append(now)
        return len(self._clients[client_ip]) <= self.max_requests

    def remaining(self, client_ip: str) -> int:
        now = time.time()
        cutoff = now - self.window_seconds
        count = len([t for t in self._clients[client_ip] if t > cutoff])
        return max(0, self.max_requests - count)


rate_limiter = RateLimiter(max_requests=120, window_seconds=60)


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件: 速率限制 + 安全头"""

    async def dispatch(self, request: Request, call_next):
        # 跳过静态资源和健康检查
        if request.url.path in ["/", "/health"] or request.url.path.startswith("/static"):
            response = await call_next(request)
            return self._add_security_headers(response)

        # 速率限制
        client_ip = request.client.host if request.client else "unknown"
        if not rate_limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

        response = await call_next(request)

        # 添加速率限制头
        remaining = rate_limiter.remaining(client_ip)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)

        return self._add_security_headers(response)

    def _add_security_headers(self, response: Response) -> Response:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# Prompt Injection 检测模式
INJECTION_PATTERNS = [
    r"(?i)(ignore|forget|disregard)\s+(all\s+)?(previous|above|earlier|prior)\s+(instructions?|prompts?|rules?)",
    r"(?i)(you\s+are\s+now|act\s+as|pretend\s+to\s+be|roleplay\s+as)",
    r"(?i)(system\s*:\s*|\[system\]|<<system>>)",
    r"(?i)(DAN\s|jailbreak|developer\s*mode)",
]


def detect_prompt_injection(text: str) -> Optional[str]:
    """检测 Prompt Injection 攻击，返回匹配的模式或 None"""
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return f"检测到潜在的安全风险输入"
    return None


def sanitize_input(text: str, max_length: int = 4000) -> str:
    """输入消毒：截断长度 + 移除控制字符"""
    # 截断
    text = text[:max_length]
    # 移除控制字符（保留换行和制表符）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text.strip()
