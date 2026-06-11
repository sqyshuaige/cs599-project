from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.agents.rag_agent import rag_query, init_knowledge_base
from app.agents.oa_agent import chat_with_agent
from app.agents.approval_graph import run_approval_workflow
from app.agents.expense_agent import analyze_expenses, detect_anomaly
from app.observability import metrics, TokenEstimator
from app.security import detect_prompt_injection, sanitize_input

router = APIRouter(prefix="/api/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []


class AutoApproveRequest(BaseModel):
    request_type: str
    request_id: int
    applicant: str
    department: str
    details: str


class ExpenseAnalysisRequest(BaseModel):
    department: Optional[str] = None


@router.post("/chat")
def agent_chat(req: ChatRequest):
    # Prompt Injection 检测
    injection = detect_prompt_injection(req.message)
    if injection:
        raise HTTPException(status_code=400, detail=injection)

    # 输入消毒
    sanitized = sanitize_input(req.message)

    result = chat_with_agent(sanitized, req.history)

    # Token 消耗追踪
    metrics.record_llm_call(
        TokenEstimator.estimate_input(sanitized),
        TokenEstimator.estimate_output(result),
    )

    return {"response": result}


@router.post("/rag/query")
def query_knowledge(question: dict):
    q = sanitize_input(question.get("question", ""))
    response = rag_query(q)
    metrics.record_llm_call(
        TokenEstimator.estimate_input(q),
        TokenEstimator.estimate_output(response),
    )
    return {"response": response}


@router.post("/rag/init")
def init_rag():
    init_knowledge_base()
    return {"status": "knowledge base initialized"}


@router.post("/approve/auto")
def auto_approve(req: AutoApproveRequest):
    injection = detect_prompt_injection(req.details)
    if injection:
        raise HTTPException(status_code=400, detail=injection)

    result = run_approval_workflow(
        request_type=req.request_type,
        request_id=req.request_id,
        applicant=sanitize_input(req.applicant),
        department=req.department,
        details=sanitize_input(req.details),
    )

    metrics.record_llm_call(
        TokenEstimator.estimate_input(req.details),
        TokenEstimator.estimate_output(str(result)),
    )
    return result


@router.post("/expense/analyze")
def expense_analysis(req: ExpenseAnalysisRequest):
    result = analyze_expenses(department=req.department)
    metrics.record_llm_call(
        TokenEstimator.estimate_input("全量报销数据分析"),
        TokenEstimator.estimate_output(str(result)),
    )
    return result


@router.post("/expense/anomaly/{expense_id}")
def expense_anomaly(expense_id: int):
    result = detect_anomaly(expense_id)
    metrics.record_llm_call(
        TokenEstimator.estimate_input(f"检测报销异常 ID={expense_id}"),
        TokenEstimator.estimate_output(str(result)),
    )
    return result
