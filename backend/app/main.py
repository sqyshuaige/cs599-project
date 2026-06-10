import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.database import engine, Base
from app.routers import leave, expense, meeting, announcement, agent
from app.observability import ObservabilityMiddleware, get_health_status, metrics, TokenEstimator
from app.security import SecurityMiddleware, detect_prompt_injection, sanitize_input

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "frontend")

app = FastAPI(
    title="AgentBridge - 智慧OA系统",
    version="2.0.0",
    description="企业级OA系统的Agent智能化改造 - 支持MCP协议、生产级可观测性与安全防护",
)

# ---- 中间件（按顺序添加）----

# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 安全中间件（速率限制 + 安全头）
app.add_middleware(SecurityMiddleware)

# 3. 可观测性中间件（日志 + 计时 + 统计）
app.add_middleware(ObservabilityMiddleware)


# ---- 路由注册 ----

app.include_router(leave.router)
app.include_router(expense.router)
app.include_router(meeting.router)
app.include_router(announcement.router)
app.include_router(agent.router)


# ---- 生命周期 ----

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    from app.seed import seed_data
    seed_data()


@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ---- 健康检查与监控端点 ----

@app.get("/health")
def health_check():
    """健康检查端点 - 返回系统状态和累计指标"""
    return get_health_status()


@app.get("/health/live")
def liveness():
    """Kubernetes Liveness Probe"""
    return {"status": "alive"}


@app.get("/health/ready")
def readiness():
    """Kubernetes Readiness Probe"""
    status = get_health_status()
    if status["database"] == "error":
        return JSONResponse(status_code=503, content={"status": "not ready", "reason": "database connection failed"})
    return {"status": "ready"}


@app.get("/metrics")
def get_metrics():
    """Prometheus 兼容的指标端点"""
    s = metrics.get_summary()
    return {
        "uptime_seconds": s["uptime_seconds"],
        "http_requests_total": s["total_requests"],
        "http_errors_total": s["total_errors"],
        "llm_calls_total": s["total_llm_calls"],
        "llm_input_tokens_total": s["total_input_tokens"],
        "llm_output_tokens_total": s["total_output_tokens"],
        "llm_cost_rmb_total": s["estimated_cost_rmb"],
    }
