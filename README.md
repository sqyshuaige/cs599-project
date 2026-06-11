# AgentBridge - 智慧OA系统Agent智能化改造

> **课程**：企业级应用软件设计与开发（CS599）
> **方向**：方向二 - 企业级应用软件的 Agent 改造
> **学期**：2025-2026 春季

---

## 项目简介

**AgentBridge** 是一个基于 Agentic AI 技术对传统企业OA系统进行智能化改造的项目。通过在模拟OA系统（请假管理、报销管理、会议室预定、公告管理）的基础上，集成 DeepSeek LLM + LangGraph + Function Calling + RAG + MCP 技术栈，实现了自然语言交互、智能审批、异常检测和知识问答等核心 AI 能力，同时达到速率限制、Prompt Injection 防护、Token 追踪、容器化部署等生产级标准。

### 改造前 vs 改造后

| 维度 | 改造前 | 改造后 |
|------|--------|--------|
| 交互方式 | 表单驱动，6次页面跳转 | 对话驱动，一句自然语言完成 |
| 审批周期 | 人工审批 1-3 天 | AI秒级分析 + 人工按需介入 |
| 制度查询 | 翻阅多种文档 | RAG 语义检索秒级应答 |
| 异常检测 | 人工抽查，盲区多 | LLM 全量语义分析自动标记 |
| 安全防护 | 无 | 速率限制 + PromptInjection检测 + 安全头 |
| 协议标准 | 仅内部调用 | Function Calling + MCP双通道 |
| 部署方式 | 手动脚本 | Docker多阶段构建 + 健康检查 |

## 技术覆盖

| 核心技术要素 | 实现方式 |
|-------------|---------|
| SDD 规格驱动开发 | Product / Architecture / API Spec 三层规格文档 |
| Function Calling | 9个Tool函数，LLM自主选择调用 |
| MCP 协议 | 标准 MCP Server，stdio 传输，JSON Schema 定义 |
| Agentic RAG | ChromaDB + text-embedding-3-small + 语义检索 |
| 状态管理与多步推理 | LangGraph 4步审批状态机（analyze→check_policy→decide→execute） |
| 可观测性 | 结构化日志 + Token追踪/成本估算 + /health三级端点 + /metrics |

## 快速开始

### 环境要求

- Python 3.11+
- DeepSeek API Key

### 本地启动

```bash
cd cs599-project/src/backend
pip install -r requirements.txt
copy ..\..\.env.example .env          # 编辑 .env 填入 DEEPSEEK_API_KEY
python -m uvicorn app.main:app --reload --port 8000
```
浏览器打开 `http://127.0.0.1:8000`

### Docker 一键部署

```bash
cd cs599-project
echo "DEEPSEEK_API_KEY=sk-xxx" > .env
docker compose up -d --build
curl http://localhost:8000/health
```

## 项目结构

```
cs599-project/
├── src/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI 入口 + 中间件注册 + 健康检查/指标端点
│   │   │   ├── config.py            # Pydantic Settings 环境变量配置
│   │   │   ├── database.py          # SQLAlchemy 数据库连接
│   │   │   ├── models.py            # 5张数据表 ORM 模型
│   │   │   ├── seed.py              # 种子测试数据
│   │   │   ├── mcp_server.py        # MCP协议服务端（9工具，stdio传输）
│   │   │   ├── security.py          # 速率限制 + PromptInjection + 安全头
│   │   │   ├── observability.py     # 日志 + Token追踪 + 健康检查
│   │   │   ├── agents/
│   │   │   ├── oa_agent.py      # OA对话Agent (Function Calling)
│   │   │   ├── rag_agent.py     # RAG知识库Agent (ChromaDB + Embedding)
│   │   │   ├── approval_graph.py # 审批Agent (LangGraph 四步状态机)
│   │   │   └── expense_agent.py # 报销异常分析Agent
│   │   │   └── routers/
│   │   │       ├── leave.py     # 请假CRUD API
│   │   │       ├── expense.py   # 报销CRUD API
│   │   │       ├── meeting.py   # 会议室API
│   │   │       ├── announcement.py  # 公告API
│   │   │       └── agent.py     # Agent API（含安全检测 + Token追踪）
│   │   └── requirements.txt
│   ├── frontend/
│   │   └── index.html           # SPA 单页应用
│   └── tests/
│       └── test_api.py          # 7个pytest自动化测试用例
├── docs/
│   ├── CS599_大作业报告.pdf      # 最终提交报告
│   └── specs/                   # SDD三层规格文档
├── Dockerfile                   # 多阶段构建 + 非root用户 + HEALTHCHECK
├── docker-compose.yml           # 生产级编排（volumes + restart + 资源限制）
├── LICENSE                      # MIT 开源协议
├── .gitignore
└── README.md
```

## 技术栈

| 类别 | 技术 |
|------|------|
| AI IDE | Trae CN |
| LLM | DeepSeek API (deepseek-chat) |
| Embedding | OpenAI text-embedding-3-small |
| Agent 框架 | LangChain + LangGraph |
| 协议 | Function Calling + MCP (Model Context Protocol) |
| 向量数据库 | ChromaDB |
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 安全 | 速率限制 + Prompt Injection 检测 + CSP/HSTS安全头 |
| 可观测 | Loguru结构化日志 + Token追踪/成本估算 + 三级健康检查 |
| 部署 | Docker + Docker Compose (多阶段构建/非root/HEALTHCHECK) |

## 开源协议

MIT License

## 引用声明

- LangChain: https://github.com/langchain-ai/langchain
- LangGraph: https://github.com/langchain-ai/langgraph
- ChromaDB: https://github.com/chroma-core/chroma
- FastAPI: https://github.com/tiangolo/fastapi
- DeepSeek API: https://api-docs.deepseek.com
- MCP: https://github.com/modelcontextprotocol
