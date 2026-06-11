# Product Spec - AgentBridge

## 1. 产品概述

### 1.1 产品定义

AgentBridge 是在模拟传统企业OA系统（请假管理、报销管理、会议室预定、公告管理四大模块）基础上，通过集成Agentic AI能力实现的智能化升级版本。改造前，系统以表单驱动为核心，员工需手动登录、逐字段填写申请，审批完全依赖人工逐级审查，公司政策分散于多个文档中缺乏统一检索，报销审核缺少自动化异常检测能力且安全防护基本空白。改造后，原始OA系统保留完整的数据模型和业务API，新增的Agent层以非侵入方式提供四项AI增强能力：自然语言交互、智能审批辅助、RAG知识问答、全量报销异常分析。同时，系统集成了MCP协议支持将九项业务工具通过标准化协议暴露给外部AI客户端，并达到了速率限制、Prompt Injection检测、安全响应头、Token追踪、容器化部署等生产级标准。

### 1.2 原始系统痛点

- 操作繁琐：每次申请需填写多个字段，涉及6次以上页面跳转，平均耗时3-5分钟
- 审批延迟：人工审批受时间和精力限制，平均审批周期1-3天
- 信息检索困难：公司制度分散于多个文档，新员工查找困难
- 缺乏风控：报销异常依赖人工发现，固定规则引擎无法识别跨记录异常模式
- 安全盲区：无速率限制、无输入安全校验、缺乏请求审计日志

### 1.3 改造前后对比

| 维度 | 改造前 | 改造后 |
|------|--------|--------|
| 交互方式 | 表单驱动，6次页面跳转 | 对话驱动，一句自然语言完成 |
| 审批周期 | 人工审批 1-3 天 | AI秒级分析 + 人工按需介入 |
| 制度查询 | 翻阅多种文档 | RAG语义检索秒级应答 |
| 异常检测 | 人工抽查，盲区多 | LLM全量语义分析自动标记 |
| 安全防护 | 无 | 速率限制 + PromptInjection检测 + 安全头 + 输入消毒 |
| 协议标准 | 仅内部调用 | Function Calling + MCP双通道 |
| 可观测性 | 无 | 结构化日志 + Token追踪/成本估算 + 三级健康检查 |
| 部署方式 | 手动脚本 | Docker多阶段构建 + 健康检查 + 资源限制 |

## 2. 核心功能

### 2.1 智能对话（Function Calling）
- 九个工具函数覆盖查询、创建、审批三类操作
- LLM自动解析自然语言意图，自主决定工具调用时机和参数
- 对话历史管理，支持追问和上下文理解

### 2.2 智能审批Agent（LangGraph状态机）
- 四步审批工作流：分析→政策审核→决策→执行
- LLM语义分析叠加硬规则校验的双重保障
- 风险分级（低/中/高），高风险自动标记需人工介入

### 2.3 知识库问答（RAG）
- ChromaDB向量数据库存储制度知识，text-embedding-3-small生成1536维向量
- 语义级精准检索，LLM综合生成带来源引用的答案

### 2.4 报销异常分析
- 全量报销数据四维度统计预处理（金额、类别、时间、描述）
- LLM语义级关联分析识别异常模式，自动标记并生成风险报告

### 2.5 MCP协议集成
- 标准MCP Server通过stdio传输协议对外暴露九项业务工具
- 完整JSON Schema定义（类型系统、必填字段、参数描述）
- 兼容Claude Desktop、Cursor等外部AI客户端

### 2.6 生产级安全防护
- IP级别滑动窗口速率限制（120次/60秒），超限返回429
- Prompt Injection检测引擎（四类正则模式匹配），危险输入返回400
- 标准安全响应头注入（CSP、HSTS、X-Frame-Options、X-Content-Type-Options）
- 输入消毒（长度截断2000字符+控制字符过滤）

### 2.7 生产级可观测性
- Loguru结构化JSON日志，自动轮转（10MB保留，30天归档）
- 每次LLM调用追踪Token消耗并按DeepSeek官方定价估算人民币成本
- /health三级端点（综合、存活、就绪）支持Kubernetes/Docker自动探活
- /metrics端点Prometheus兼容格式暴露累计指标

### 2.8 容器化部署
- Docker多阶段构建（builder+runtime）减小镜像体积
- 非root用户运行，HEALTHCHECK指令自动健康监控
- docker-compose一键部署，restart策略+内存限制+日志轮转
- 部署文档覆盖Docker Compose、Render、Railway三种方式

## 3. 用户角色

- 普通员工：通过自然语言创建申请、查询审批进度、RAG知识问答
- 部门经理：审批申请、查看团队数据、接收异常预警
- 系统管理员：维护知识库、查看健康检查和指标端点

## 4. 技术栈

| 类别 | 技术 |
|------|------|
| AI IDE | Trae CN |
| LLM | DeepSeek API (deepseek-chat) |
| Embedding | OpenAI text-embedding-3-small |
| Agent框架 | LangChain + LangGraph |
| 协议 | Function Calling + MCP |
| 向量数据库 | ChromaDB |
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 安全 | 速率限制 + Prompt Injection检测 + CSP/HSTS + 输入消毒 |
| 可观测 | Loguru + Token追踪/成本估算 + /health + /metrics |
| 部署 | Docker + Docker Compose（非root/HEALTHCHECK/资源限制） |
