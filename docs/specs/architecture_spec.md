# Architecture Spec - AgentBridge

## 1. 系统分层架构

系统采用四层架构，各层通过标准HTTP/REST协议通信，Agent层以非侵入方式叠加于原有业务API之上。

**前端展示层**：基于原生HTML5、CSS3、JavaScript构建单页应用，包含控制台、请假管理、报销管理、会议室管理、公告管理和AI聊天面板六个功能区域。

**FastAPI应用层**：包含五个路由模块（leave、expense、meeting、announcement、agent）实现RESTful API端点，负责请求路由、参数校验和响应序列化。在应用层与Agent层之间横切了两个中间件：SecurityMiddleware负责IP级别滑动窗口速率限制（120次/60秒）和安全响应头注入（CSP、HSTS、X-Frame-Options）；ObservabilityMiddleware负责请求日志、响应计时和全局指标收集。

**Agent编排层**：包含四个独立Agent模块。OA对话Agent基于Function Calling协议将九项业务工具包装为LLM可调用的工具函数；审批Agent基于LangGraph状态机实现四步审批工作流（分析→政策审核→决策→执行）；分析Agent基于LLM实现全量报销数据的异常检测；RAG知识Agent基于ChromaDB和text-embedding-3-small实现制度知识的向量检索与生成。四个Agent均通过统一LLM抽象层调用DeepSeek API。

**基础设施层**：包含SQLite业务数据库、ChromaDB向量数据库和DeepSeek API外部服务，分别承载业务数据持久化、向量化知识存储和大模型推理。

在架构外侧，MCP Server模块通过stdio传输协议将九项业务工具以标准JSON Schema向外暴露，兼容Claude Desktop等外部AI客户端。Docker容器化层提供多阶段构建、非root用户运行、HEALTHCHECK健康检查和资源限制等生产级部署保障。

系统架构详见文档目录下的架构图。

## 2. Agent 交互流程

### 2.1 OA对话Agent流程

用户输入自然语言后，先经过Prompt Injection检测和输入消毒处理，再与系统提示词一并发送给LLM。LLM分析意图并决定是否需要调用工具函数：若需要，LLM返回Function Call指令，Agent执行对应的业务工具（如调用query_leave_status查询数据库），将工具返回结果交还LLM整合为自然语言回复；若不需要，直接生成回复。整个过程中每次LLM调用均追踪Token量并估算人民币成本。

### 2.2 审批Agent工作流（LangGraph状态机）

审批请求进入后依次经过四个节点。分析节点：Agent读取申请完整内容并提取关键信息，评估风险等级（低/中/高）。政策审核节点：在LLM分析基础上叠加硬规则——如报销金额超过20,000元自动提升风险等级为高——形成语义分析加规则校验的双重保障。决策节点：综合前期分析和审核结果，调用LLM做出最终决策并生成审批理由。执行节点：将审批结果写入数据库，更新申请状态、审批建议和审批人信息。

每个节点均由LLM驱动，节点之间通过TypedDict状态对象传递上下文。高风险申请自动标记为"需人工介入"。整个工作流外层包裹try/except，确保LLM调用异常时返回可用值而非崩溃。

### 2.3 RAG知识Agent流程

初始化阶段：将Markdown制度文档通过RecursiveCharacterTextSplitter切分为语义段落，经text-embedding-3-small生成1536维向量，存入ChromaDB形成可检索的向量索引。运行时阶段：用户问题经Embedding转换为向量后，在ChromaDB中执行语义相似度检索，取回最相关文档片段作为上下文拼接至Prompt，由LLM生成带来源引用的答案。

### 2.4 报销异常分析Agent流程

Agent读取全量报销数据后，对每条报销执行金额规模、类别分布、时间频率和描述内容四个维度的统计预处理，然后将结构化统计结果发送给LLM进行语义级异常分析，识别金额显著偏离同类均值、同一申请人短期内高频提交、报销描述与实际票据类型不匹配等异常模式，最终标记至对应记录的异常字段并生成分析报告。

### 2.5 MCP协议交互流程

外部AI客户端启动MCP Server子进程建立stdio通信通道，通过list_tools获取九个工具的函数签名和完整JSON Schema定义。用户以自然语言提出业务需求时，客户端LLM分析意图后通过call_tool发送调用指令，MCP Server在独立线程池中执行数据库操作并返回结果。此流程与OA系统内部Agent调用完全隔离，体现了外部协议层与内部业务层的解耦设计。

## 3. 数据流设计

系统包含四条主要数据通路：

**业务数据流**：前端表单或AI对话提交请求，经FastAPI路由校验参数，通过SQLAlchemy ORM持久化至SQLite数据库，初始状态为待审批，审批完成后写回更新。

**Agent调用链**：用户输入经/api/agent/chat路由分发至OA对话Agent，Agent通过Function Calling调用DeepSeek LLM进行推理，LLM返回的函数调用指令驱动工具函数查询SQLite，结果交还LLM二次整合后返回用户。所有Agent调用共享统一LLM抽象层，模型切换仅需修改一处配置。

**知识数据流**：Markdown制度文档经文本切分后通过text-embedding-3-small向量化存入ChromaDB；问答时用户问题向量化后在ChromaDB中语义检索相关段落，作为上下文注入LLM生成答案。

**监控与安全数据流**：每个HTTP请求流经可观测性中间件时自动生成唯一request_id并记录完整日志（方法、路径、状态码、耗时），LLM调用自动累计Token量和成本估算，累计指标通过/metrics端点以Prometheus兼容格式对外暴露，健康状态通过/health三级端点供容器编排平台探活。安全数据通路方面，每个请求先经由安全中间件进行IP级别速率限制校验和标准安全头注入，Agent对话额外经过Prompt Injection检测和输入消毒处理。

## 4. Agent设计模式

本项目采用三种Agent设计模式：

- **Tool Use Agent模式**用于OA对话Agent，通过Function Calling协议将业务能力暴露为工具函数，由LLM自主决定工具调用时机和参数
- **State Machine Agent模式**用于审批Agent，基于LangGraph定义四步状态机，每个状态节点由LLM驱动推理，节点之间的转移由状态条件控制
- **RAG Agent模式**用于知识问答Agent，结合向量检索和LLM生成，实现外部知识增强的精准问答

## 5. 技术栈总览

| 层次 | 技术选型 |
|------|---------|
| 前端 | HTML5 + CSS3 + Vanilla JS |
| 后端框架 | FastAPI |
| LLM | DeepSeek API (deepseek-chat) |
| Embedding | text-embedding-3-small |
| ORM | SQLAlchemy |
| 数据库 | SQLite（业务数据）+ ChromaDB（向量） |
| Agent框架 | LangChain + LangGraph |
| 协议 | Function Calling + MCP (Model Context Protocol) |
| 安全 | 速率限制 + Prompt Injection检测 + CSP/HSTS安全头 + 输入消毒 |
| 可观测 | Loguru结构化日志 + Token追踪/成本估算 + 三级健康检查 + /metrics |
| 部署 | Docker多阶段构建 + docker-compose（非root/HEALTHCHECK/内存限制/日志轮转） |
