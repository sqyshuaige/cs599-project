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
Response: `[{id, applicant, department, leave_type, start_date, end_date, reason, status, agent_suggestion}]`

### 1.2 创建请假申请
```
POST /api/leave/
```
Request: `{applicant, department, leave_type, start_date, end_date, reason}`

### 1.3 审批请假
```
POST /api/leave/{id}/approve
```
Request: `{status, approver, approval_comment}`

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
Request: `{applicant, department, category, amount, description}`

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
Request: `{message, history}` — 内置Prompt Injection检测和输入消毒，每次调用自动追踪Token消耗

### 5.2 RAG知识问答
```
POST /api/agent/rag/query
```
Request: `{question}` — 问题经Embedding向量化后在ChromaDB中检索，LLM综合生成答案

### 5.3 自动审批
```
POST /api/agent/approve/auto
```
Request: `{request_type, request_id, applicant, department, details}` — 执行LangGraph四步审批工作流，返回risk_level、suggestion、final_decision、reason

### 5.4 报销异常分析
```
POST /api/agent/expense/analyze
```
Request: `{department?}` — 全量报销多维度语义级关联分析，返回summary、anomalies列表、suggestions

### 5.5 单笔异常检测
```
POST /api/agent/expense/anomaly/{expense_id}
```

---

## 6. 系统监控 API

### 6.1 综合健康检查
```
GET /health
```
Response: `{status, version, database, chromadb, metrics}` — metrics包含uptime_seconds、total_requests、total_errors、error_rate、llm_calls、token量和成本估算

### 6.2 存活探针
```
GET /health/live
```
Response: `{"status": "alive"}` — 用于Kubernetes Liveness Probe

### 6.3 就绪探针
```
GET /health/ready
```
Response: 数据库正常时200，异常时503 — 用于Kubernetes Readiness Probe

### 6.4 指标端点
```
GET /metrics
```
Response: `{uptime_seconds, http_requests_total, http_errors_total, llm_calls_total, llm_input_tokens_total, llm_output_tokens_total, llm_cost_rmb_total}` — Prometheus兼容格式

---

## 7. Agent工具函数（Function Calling + MCP协议）

九个工具函数同时通过Function Calling（内部Agent调用）和MCP协议（外部AI客户端调用）两种通道暴露。

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| query_leave_status | 查询员工请假状态 | applicant |
| query_all_leaves | 查询全量请假记录 | 无 |
| create_leave_request | 创建请假申请 | applicant, department, leave_type, start_date, end_date, reason |
| query_expense_status | 查询员工报销状态 | applicant |
| query_all_expenses | 查询全量报销记录 | 无 |
| create_expense_request | 创建报销申请 | applicant, department, category, amount, description |
| query_meeting_rooms | 查询所有会议室信息 | 无 |
| query_announcements | 查询所有公告列表 | 无 |
| approve_leave | 审批请假申请 | leave_id, status, approver, comment |

所有工具函数运行在独立SQLAlchemy数据库会话中，操作完成后通过finally确保连接释放，事务一致性。MCP Server通过stdio传输协议、JSON Schema完整类型定义暴露上述九项工具，兼容Claude Desktop、Cursor等客户端。
