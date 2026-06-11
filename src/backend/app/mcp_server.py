"""
MCP (Model Context Protocol) Server
将 OA 系统的 9 个工具函数通过 MCP 协议暴露给外部 AI 客户端
支持 stdio 传输方式

使用方法:
  python -m app.mcp_server
  或在 Claude Desktop / Cursor 等客户端中配置此 MCP Server
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.server.models import InitializationOptions

from app.database import SessionLocal
from app.models import (
    LeaveRequest, ExpenseReport, MeetingRoom, Announcement,
    ApprovalStatus, LeaveType
)

mcp_server = Server("oa-mcp-server")


def get_db():
    return SessionLocal()


async def run_tool(func):
    """在线程池中执行数据库操作"""
    return await asyncio.to_thread(func)


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_leave_status",
            description="查询某位员工的请假申请状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "applicant": {"type": "string", "description": "员工姓名"}
                },
                "required": ["applicant"],
            },
        ),
        Tool(
            name="query_all_leaves",
            description="查询所有请假记录（全量查询，不限定员工）",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="create_leave_request",
            description="创建请假申请",
            inputSchema={
                "type": "object",
                "properties": {
                    "applicant": {"type": "string", "description": "员工姓名"},
                    "department": {"type": "string", "description": "所属部门"},
                    "leave_type": {"type": "string", "description": "请假类型：年假/病假/事假/婚假/产假"},
                    "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
                    "reason": {"type": "string", "description": "请假原因"},
                },
                "required": ["applicant", "department", "leave_type", "start_date", "end_date", "reason"],
            },
        ),
        Tool(
            name="query_expense_status",
            description="查询某位员工的报销单状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "applicant": {"type": "string", "description": "员工姓名"}
                },
                "required": ["applicant"],
            },
        ),
        Tool(
            name="query_all_expenses",
            description="查询所有报销记录（全量查询，不限定员工）",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="create_expense_request",
            description="创建报销申请",
            inputSchema={
                "type": "object",
                "properties": {
                    "applicant": {"type": "string", "description": "员工姓名"},
                    "department": {"type": "string", "description": "所属部门"},
                    "category": {"type": "string", "description": "报销类别"},
                    "amount": {"type": "number", "description": "报销金额"},
                    "description": {"type": "string", "description": "报销说明"},
                },
                "required": ["applicant", "department", "category", "amount", "description"],
            },
        ),
        Tool(
            name="query_meeting_rooms",
            description="查询所有会议室信息（包括容量、位置、设备、可用状态）",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="query_announcements",
            description="查询公司最新公告",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="approve_leave",
            description="审批请假申请（通过或驳回）",
            inputSchema={
                "type": "object",
                "properties": {
                    "leave_id": {"type": "integer", "description": "请假申请ID"},
                    "status": {"type": "string", "description": "审批结果：已通过/已驳回"},
                    "approver": {"type": "string", "description": "审批人姓名"},
                    "comment": {"type": "string", "description": "审批意见（可选）"},
                },
                "required": ["leave_id", "status", "approver"],
            },
        ),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        if name == "query_leave_status":
            result = await run_tool(lambda: _query_leave_status(arguments["applicant"]))
        elif name == "query_all_leaves":
            result = await run_tool(_query_all_leaves)
        elif name == "create_leave_request":
            result = await run_tool(lambda: _create_leave_request(
                arguments["applicant"], arguments["department"],
                arguments["leave_type"], arguments["start_date"],
                arguments["end_date"], arguments["reason"]
            ))
        elif name == "query_expense_status":
            result = await run_tool(lambda: _query_expense_status(arguments["applicant"]))
        elif name == "query_all_expenses":
            result = await run_tool(_query_all_expenses)
        elif name == "create_expense_request":
            result = await run_tool(lambda: _create_expense_request(
                arguments["applicant"], arguments["department"],
                arguments["category"], float(arguments["amount"]),
                arguments["description"]
            ))
        elif name == "query_meeting_rooms":
            result = await run_tool(_query_meeting_rooms)
        elif name == "query_announcements":
            result = await run_tool(_query_announcements)
        elif name == "approve_leave":
            result = await run_tool(lambda: _approve_leave(
                int(arguments["leave_id"]), arguments["status"],
                arguments["approver"], arguments.get("comment", "")
            ))
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ---- 工具实现函数 (与 oa_agent.py 中保持一致) ----

def _query_leave_status(applicant: str) -> str:
    db = get_db()
    try:
        leaves = db.query(LeaveRequest).filter(
            LeaveRequest.applicant == applicant
        ).order_by(LeaveRequest.created_at.desc()).limit(10).all()
        if not leaves:
            return f"No leave records found for {applicant}."
        result = [{
            "id": l.id, "leave_type": l.leave_type.value,
            "start_date": l.start_date.strftime("%Y-%m-%d"),
            "end_date": l.end_date.strftime("%Y-%m-%d"),
            "status": l.status.value, "reason": l.reason,
        } for l in leaves]
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


def _query_all_leaves() -> str:
    db = get_db()
    try:
        leaves = db.query(LeaveRequest).order_by(
            LeaveRequest.created_at.desc()
        ).limit(20).all()
        if not leaves:
            return "No leave records found."
        result = [{
            "id": l.id, "applicant": l.applicant, "department": l.department,
            "leave_type": l.leave_type.value,
            "start_date": l.start_date.strftime("%Y-%m-%d"),
            "end_date": l.end_date.strftime("%Y-%m-%d"),
            "status": l.status.value, "reason": l.reason,
        } for l in leaves]
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


def _create_leave_request(applicant: str, department: str, leave_type: str,
                          start_date: str, end_date: str, reason: str) -> str:
    db = get_db()
    try:
        try:
            lt = LeaveType(leave_type)
        except ValueError:
            return f"Invalid leave_type '{leave_type}'. Valid: 年假/病假/事假/婚假/产假"
        leave = LeaveRequest(
            applicant=applicant, department=department, leave_type=lt,
            start_date=datetime.strptime(start_date, "%Y-%m-%d"),
            end_date=datetime.strptime(end_date, "%Y-%m-%d"),
            reason=reason,
        )
        db.add(leave); db.commit(); db.refresh(leave)
        return f"Leave request created. ID={leave.id}, status=pending"
    finally:
        db.close()


def _query_expense_status(applicant: str) -> str:
    db = get_db()
    try:
        expenses = db.query(ExpenseReport).filter(
            ExpenseReport.applicant == applicant
        ).order_by(ExpenseReport.created_at.desc()).limit(10).all()
        if not expenses:
            return f"No expense records found for {applicant}."
        result = [{
            "id": e.id, "category": e.category, "amount": e.amount,
            "status": e.status.value, "description": e.description,
        } for e in expenses]
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


def _query_all_expenses() -> str:
    db = get_db()
    try:
        expenses = db.query(ExpenseReport).order_by(
            ExpenseReport.created_at.desc()
        ).limit(20).all()
        if not expenses:
            return "No expense records found."
        result = [{
            "id": e.id, "applicant": e.applicant, "department": e.department,
            "category": e.category, "amount": e.amount,
            "status": e.status.value, "description": e.description,
        } for e in expenses]
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


def _create_expense_request(applicant: str, department: str, category: str,
                            amount: float, description: str) -> str:
    db = get_db()
    try:
        expense = ExpenseReport(
            applicant=applicant, department=department,
            category=category, amount=amount, description=description,
        )
        db.add(expense); db.commit(); db.refresh(expense)
        return f"Expense created. ID={expense.id}, amount={amount}, status=pending"
    finally:
        db.close()


def _query_meeting_rooms() -> str:
    db = get_db()
    try:
        rooms = db.query(MeetingRoom).all()
        result = [{
            "id": r.id, "name": r.name, "capacity": r.capacity,
            "location": r.location, "equipment": r.equipment,
            "available": r.is_available,
        } for r in rooms]
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


def _query_announcements() -> str:
    db = get_db()
    try:
        announcements = db.query(Announcement).order_by(
            Announcement.is_pinned.desc(), Announcement.created_at.desc()
        ).limit(10).all()
        if not announcements:
            return "No announcements."
        result = [{
            "id": a.id, "title": a.title, "content": a.content[:100],
            "publisher": a.publisher,
        } for a in announcements]
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


def _approve_leave(leave_id: int, status: str, approver: str, comment: str = "") -> str:
    db = get_db()
    try:
        leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
        if not leave:
            return f"Leave request ID={leave_id} not found."
        try:
            approval_status = ApprovalStatus(status)
        except ValueError:
            return f"Invalid status '{status}'. Valid: 已通过/已驳回"
        leave.status = approval_status
        leave.approver = approver
        leave.approval_comment = comment
        db.commit()
        return f"Leave ID={leave_id} {status}. Approver: {approver}"
    finally:
        db.close()


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream, write_stream,
            InitializationOptions(
                server_name="oa-mcp-server",
                server_version="2.0.0",
                capabilities={},
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
