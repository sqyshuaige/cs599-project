# API Spec - AgentBridge

## 基础信息

- Base URL: `http://localhost:8000`
- Content-Type: `application/json`

---

## 1. 请假管理 API

### 1.1 获取请假列表
```
GET /api/leave/?status=待审批
```
Response:
```json
[{
  "id": 1,
  "applicant": "张三",
  "department": "技术研发部",
  "leave_type": "年假",
  "start_date": "2025-06-15T00:00:00",
  "end_date": "2025-06-17T00:00:00",
  "reason": "回老家探亲",
  "status": "待审批",
  "agent_suggestion": ""
}]
```

### 1.2 创建请假申请
```
POST /api/leave/
```
Request:
```json
{
  "applicant": "张三",
  "department": "技术研发部",
  "leave_type": "年假",
  "start_date": "2025-06-15T00:00:00",
  "end_date": "2025-06-17T00:00:00",
  "reason": "回老家探亲"
}
```

### 1.3 审批请假
```
POST /api/leave/{id}/approve
```
Request:
```json
{
  "status": "已通过",
  "approver": "AI智能审批",
  "approval_comment": "符合请假制度"
}
```

---

## 2. 报销管理 API

### 2.1 获取报销列表
```
GET /api/expense/?status=待审批
```

### 2.2 创建报销申请
```
POST /api/expense/
```
Request:
```json
{
  "applicant": "张三",
  "department": "技术研发部",
  "category": "差旅费",
  "amount": 3200.00,
  "description": "赴上海参加AI技术峰会"
}
```

### 2.3 审批报销
```
POST /api/expense/{id}/approve
```

---

## 3. 会议室 API

### 3.1 获取会议室列表
```
GET /api/meeting/rooms
```

### 3.2 预定会议室
```
POST /api/meeting/bookings
```

---

## 4. 公告 API

### 4.1 获取公告列表
```
GET /api/announcement/
```

### 4.2 创建公告
```
POST /api/announcement/
```

---

## 5. AI Agent API

### 5.1 智能对话
```
POST /api/agent/chat
```
Request:
```json
{
  "message": "查询张三的请假状态",
  "history": []
}
```
Response:
```json
{
  "response": "张三目前有1条请假记录：...\n\n📚 参考来源：请假管理制度"
}
```

### 5.2 RAG知识问答
```
POST /api/agent/rag/query
```
Request:
```json
{"question": "年假有多少天？"}
```

### 5.3 自动审批
```
POST /api/agent/approve/auto
```
Request:
```json
{
  "request_type": "leave",
  "request_id": 1,
  "applicant": "张三",
  "department": "技术研发部",
  "details": "年假申请，6月15日-17日，回老家探亲"
}
```
Response:
```json
{
  "risk_level": "低",
  "suggestion": "符合年假制度，建议批准",
  "final_decision": "通过",
  "reason": "符合公司年假管理制度"
}
```

### 5.4 报销分析
```
POST /api/agent/expense/analyze
```
Response:
```json
{
  "summary": "发现1笔异常报销",
  "anomalies": [{"id": 4, "reason": "差旅费金额8500元明显高于同类平均值3850元"}],
  "suggestions": "建议人工复查"
}
```

### 5.5 单笔异常检测
```
POST /api/agent/expense/anomaly/{expense_id}
```

---

## 6. Agent工具函数（Function Calling）

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| query_leave_status | 查询请假状态 | applicant |
| create_leave_request | 创建请假 | applicant, department, leave_type, start_date, end_date, reason |
| query_expense_status | 查询报销状态 | applicant |
| create_expense_request | 创建报销 | applicant, department, category, amount, description |
| query_meeting_rooms | 查询会议室 | 无 |
| query_announcements | 查询公告 | 无 |
| approve_leave | 审批请假 | leave_id, status, approver, comment |
