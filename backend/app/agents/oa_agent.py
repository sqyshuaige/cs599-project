import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import LeaveRequest, ExpenseReport, MeetingRoom, MeetingBooking, Announcement, ApprovalStatus, LeaveType
from app.observability import metrics, TokenEstimator


def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=temperature,
    )


SYSTEM_PROMPT = """你是「AgentBridge」——一个企业级智能办公助理。你可以帮助员工完成以下操作：

1. 查询请假申请状态、创建请假申请
2. 查询报销单状态、创建报销单
3. 查询会议室和预定信息
4. 查询公司公告
5. 解答公司政策和流程问题

请用专业、友好的语气回复。如果用户的问题涉及具体操作，请调用相应的工具函数。
如果查询不到相关信息，请如实告知用户。

关于公司政策：
- 年假：入职满1年享5天，满3年享10天，满5年享15天
- 病假：需提供医院证明，3天以内部门经理审批，3天以上需HR审批
- 事假：每年不超过15天，需提前3天申请
- 报销：单笔不超过5000元部门经理审批，超过需总监审批
- 加班餐补：每次不超过50元
- 差旅报销：需附行程单和发票"""


@tool
def query_leave_status(applicant: str) -> str:
    """查询某位员工的请假申请状态

    Args:
        applicant: 员工姓名
    """
    db: Session = SessionLocal()
    try:
        leaves = db.query(LeaveRequest).filter(
            LeaveRequest.applicant == applicant
        ).order_by(LeaveRequest.created_at.desc()).limit(10).all()
        if not leaves:
            return f"未找到 {applicant} 的请假记录。"
        result = []
        for l in leaves:
            result.append({
                "id": l.id,
                "类型": l.leave_type.value,
                "开始": l.start_date.strftime("%Y-%m-%d"),
                "结束": l.end_date.strftime("%Y-%m-%d"),
                "状态": l.status.value,
                "原因": l.reason,
            })
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


@tool
def create_leave_request(applicant: str, department: str, leave_type: str, start_date: str, end_date: str, reason: str) -> str:
    """创建请假申请

    Args:
        applicant: 员工姓名
        department: 所属部门
        leave_type: 请假类型（年假/病假/事假/婚假/产假）
        start_date: 开始日期，格式YYYY-MM-DD
        end_date: 结束日期，格式YYYY-MM-DD
        reason: 请假原因
    """
    db: Session = SessionLocal()
    try:
        try:
            lt = LeaveType(leave_type)
        except ValueError:
            return f"无效的请假类型：{leave_type}。有效类型：年假/病假/事假/婚假/产假"

        from datetime import datetime
        leave = LeaveRequest(
            applicant=applicant,
            department=department,
            leave_type=lt,
            start_date=datetime.strptime(start_date, "%Y-%m-%d"),
            end_date=datetime.strptime(end_date, "%Y-%m-%d"),
            reason=reason,
        )
        db.add(leave)
        db.commit()
        db.refresh(leave)
        return f"请假申请已创建成功！申请ID：{leave.id}，状态：待审批"
    finally:
        db.close()


@tool
def query_expense_status(applicant: str) -> str:
    """查询某位员工的报销单状态

    Args:
        applicant: 员工姓名
    """
    db: Session = SessionLocal()
    try:
        expenses = db.query(ExpenseReport).filter(
            ExpenseReport.applicant == applicant
        ).order_by(ExpenseReport.created_at.desc()).limit(10).all()
        if not expenses:
            return f"未找到 {applicant} 的报销记录。"
        result = []
        for e in expenses:
            result.append({
                "id": e.id,
                "类别": e.category,
                "金额": e.amount,
                "状态": e.status.value,
                "描述": e.description,
            })
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


@tool
def create_expense_request(applicant: str, department: str, category: str, amount: float, description: str) -> str:
    """创建报销申请

    Args:
        applicant: 员工姓名
        department: 所属部门
        category: 报销类别
        amount: 报销金额
        description: 报销说明
    """
    db: Session = SessionLocal()
    try:
        expense = ExpenseReport(
            applicant=applicant,
            department=department,
            category=category,
            amount=amount,
            description=description,
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return f"报销申请已创建成功！申请ID：{expense.id}，金额：{amount}元，状态：待审批"
    finally:
        db.close()


@tool
def query_all_leaves() -> str:
    """查询所有待审批的请假申请，或查看所有请假记录（不限定具体员工）"""
    db: Session = SessionLocal()
    try:
        leaves = db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).limit(20).all()
        if not leaves:
            return "当前没有任何请假记录。"
        result = []
        for l in leaves:
            result.append({
                "id": l.id,
                "申请人": l.applicant,
                "部门": l.department,
                "类型": l.leave_type.value,
                "开始": l.start_date.strftime("%Y-%m-%d"),
                "结束": l.end_date.strftime("%Y-%m-%d"),
                "状态": l.status.value,
                "原因": l.reason,
            })
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


@tool
def query_all_expenses() -> str:
    """查询所有待审批的报销申请，或查看所有报销记录（不限定具体员工）"""
    db: Session = SessionLocal()
    try:
        expenses = db.query(ExpenseReport).order_by(ExpenseReport.created_at.desc()).limit(20).all()
        if not expenses:
            return "当前没有任何报销记录。"
        result = []
        for e in expenses:
            result.append({
                "id": e.id,
                "申请人": e.applicant,
                "部门": e.department,
                "类别": e.category,
                "金额": e.amount,
                "状态": e.status.value,
                "描述": e.description,
            })
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


@tool
def query_meeting_rooms() -> str:
    """查询所有会议室信息"""
    db: Session = SessionLocal()
    try:
        rooms = db.query(MeetingRoom).all()
        result = []
        for r in rooms:
            result.append({
                "id": r.id,
                "名称": r.name,
                "容量": r.capacity,
                "位置": r.location,
                "设备": r.equipment,
                "可用": r.is_available,
            })
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


@tool
def query_announcements() -> str:
    """查询公司最新公告"""
    db: Session = SessionLocal()
    try:
        announcements = db.query(Announcement).order_by(
            Announcement.is_pinned.desc(),
            Announcement.created_at.desc()
        ).limit(10).all()
        if not announcements:
            return "暂无公告。"
        result = []
        for a in announcements:
            result.append({
                "id": a.id,
                "标题": a.title,
                "内容": a.content[:100],
                "发布者": a.publisher,
            })
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


@tool
def approve_leave(leave_id: int, status: str, approver: str, comment: str = "") -> str:
    """审批请假申请

    Args:
        leave_id: 请假申请ID
        status: 审批结果（已通过/已驳回）
        approver: 审批人姓名
        comment: 审批意见
    """
    db: Session = SessionLocal()
    try:
        leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
        if not leave:
            return f"未找到ID为 {leave_id} 的请假申请。"

        try:
            approval_status = ApprovalStatus(status)
        except ValueError:
            return f"无效的审批状态：{status}。有效值：已通过/已驳回"

        leave.status = approval_status
        leave.approver = approver
        leave.approval_comment = comment
        db.commit()
        return f"请假申请（ID:{leave_id}）已{status}。审批人：{approver}"
    finally:
        db.close()


ALL_TOOLS = [
    query_leave_status,
    query_all_leaves,
    create_leave_request,
    query_expense_status,
    query_all_expenses,
    create_expense_request,
    query_meeting_rooms,
    query_announcements,
    approve_leave,
]


def chat_with_agent(user_message: str, conversation_history: list = None) -> str:
    try:
        llm = get_llm()
        llm_with_tools = llm.bind_tools(ALL_TOOLS)

        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        if conversation_history:
            for msg in conversation_history[-10:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(SystemMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_message))

        response = llm_with_tools.invoke(messages)

        if hasattr(response, "tool_calls") and response.tool_calls:
            messages.append(response)
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                for t in ALL_TOOLS:
                    if t.name == tool_name:
                        try:
                            result = t.invoke(tool_args)
                        except Exception as e:
                            result = f"工具调用失败: {str(e)}"
                        messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
                        break

            final_response = llm.invoke(messages)
            return final_response.content

        return response.content
    except Exception as e:
        return f"抱歉，处理您的请求时出错了：{str(e)}。请稍后重试或换个问法。"
