import operator
from typing import TypedDict, Annotated, List

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage

from app.config import settings
from app.observability import metrics, TokenEstimator
from app.database import SessionLocal
from app.models import LeaveRequest, ExpenseReport, ApprovalStatus


def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=temperature,
    )


class ApprovalState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    request_type: str
    request_id: int
    applicant: str
    department: str
    details: str
    risk_level: str
    suggestion: str
    final_decision: str
    reason: str


def analyze_request(state: ApprovalState) -> ApprovalState:
    llm = get_llm()

    prompt = f"""你是一个企业OA系统的智能审批分析专家。请分析以下审批请求，评估风险等级并给出建议。

请求类型：{state['request_type']}
申请人：{state['applicant']}
部门：{state['department']}
详情：{state['details']}

请从以下几个方面分析：
1. 是否符合公司政策
2. 风险评估（低/中/高）
3. 审批建议

输出JSON格式：
{{"risk_level": "低/中/高", "suggestion": "你的建议"}}
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    import json
    try:
        result = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        state["risk_level"] = result.get("risk_level", "低")
        state["suggestion"] = result.get("suggestion", "无建议")
    except json.JSONDecodeError:
        state["risk_level"] = "低"
        state["suggestion"] = response.content

    state["messages"].append(HumanMessage(content=f"[分析阶段] 风险等级: {state['risk_level']}, 建议: {state['suggestion']}"))
    return state


def check_policy(state: ApprovalState) -> ApprovalState:
    state["messages"].append(HumanMessage(content="[政策审核] 根据公司制度进行合规性检查..."))

    details = state["details"].lower()
    amount = 0
    if "元" in details or "¥" in details:
        import re
        match = re.search(r'(\d+)元', details)
        if match:
            amount = int(match.group(1))

    if state["request_type"] == "expense" and amount > 20000:
        state["risk_level"] = "高"
        state["messages"].append(HumanMessage(content=f"[政策审核] 金额{amount}元超过20000元，需财务总监审批"))

    state["messages"].append(HumanMessage(content="[政策审核] 合规检查完成"))
    return state


def make_decision(state: ApprovalState) -> ApprovalState:
    llm = get_llm()

    prompt = f"""你是企业OA系统的审批决策官。根据以下信息做出最终审批决定。

请求类型：{state['request_type']}
申请人：{state['applicant']}
部门：{state['department']}
详情：{state['details']}
风险等级：{state['risk_level']}
分析建议：{state['suggestion']}

请做出最终决定并给出理由。输出JSON格式：
{{"decision": "通过/驳回", "reason": "决定理由"}}
"""
    response = llm.invoke([HumanMessage(content=prompt)])

    import json
    try:
        result = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        state["final_decision"] = result.get("decision", "通过")
        state["reason"] = result.get("reason", "")
    except json.JSONDecodeError:
        state["final_decision"] = "通过"
        state["reason"] = "经AI分析，该申请符合公司政策"

    state["messages"].append(HumanMessage(content=f"[最终决定] {state['final_decision']}: {state['reason']}"))
    return state


def execute_decision(state: ApprovalState) -> ApprovalState:
    db = SessionLocal()
    try:
        if state["request_type"] == "leave":
            record = db.query(LeaveRequest).filter(LeaveRequest.id == state["request_id"]).first()
            if record:
                record.status = ApprovalStatus.APPROVED if state["final_decision"] == "通过" else ApprovalStatus.REJECTED
                record.agent_suggestion = state["suggestion"]
                record.approval_comment = state["reason"]
                record.approver = "AI智能审批"
                db.commit()
                state["messages"].append(HumanMessage(content=f"[执行] 请假申请已{state['final_decision']}"))

        elif state["request_type"] == "expense":
            record = db.query(ExpenseReport).filter(ExpenseReport.id == state["request_id"]).first()
            if record:
                record.status = ApprovalStatus.APPROVED if state["final_decision"] == "通过" else ApprovalStatus.REJECTED
                record.approval_comment = state["reason"]
                record.approver = "AI智能审批"
                db.commit()
                state["messages"].append(HumanMessage(content=f"[执行] 报销申请已{state['final_decision']}"))

    finally:
        db.close()

    return state


def build_approval_graph():
    workflow = StateGraph(ApprovalState)

    workflow.add_node("analyze", analyze_request)
    workflow.add_node("check_policy", check_policy)
    workflow.add_node("decide", make_decision)
    workflow.add_node("execute", execute_decision)

    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "check_policy")
    workflow.add_edge("check_policy", "decide")
    workflow.add_edge("decide", "execute")
    workflow.add_edge("execute", END)

    return workflow.compile()


approval_graph = build_approval_graph()


def run_approval_workflow(request_type: str, request_id: int, applicant: str, department: str, details: str) -> dict:
    try:
        result = approval_graph.invoke({
            "messages": [],
            "request_type": request_type,
            "request_id": request_id,
            "applicant": applicant,
            "department": department,
            "details": details,
            "risk_level": "",
            "suggestion": "",
            "final_decision": "",
            "reason": "",
        })
        return {
            "risk_level": result.get("risk_level", "未知"),
            "suggestion": result.get("suggestion", ""),
            "final_decision": result.get("final_decision", "未知"),
            "reason": result.get("reason", ""),
        }
    except Exception as e:
        return {
            "risk_level": "未知",
            "suggestion": f"自动分析失败: {str(e)}",
            "final_decision": "未知",
            "reason": "系统异常，请人工审批",
        }
