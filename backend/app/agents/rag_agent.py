import json
import os
from typing import List

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage

from app.config import settings

PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "chroma_db_knowledge")


def get_llm():
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=0.1,
    )


def get_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )


KNOWLEDGE_DOCS = [
    Document(
        page_content="""
公司请假管理制度（2025版）

第一条 总则
为规范公司员工请假管理，保障员工合法权益，提高工作效率，特制定本制度。

第二条 请假类型
1. 年假：员工入职满1年享5天带薪年假，满3年享10天，满5年享15天。年假可分段使用，当年有效。
2. 病假：员工因病需休息，应提供二级甲等以上医院出具的诊断证明。3天以内病假由部门经理审批，3天以上需HR部门审批。
3. 事假：因私事需要请假，每年累计不超过15天。事假需提前3个工作日申请，紧急情况除外。
4. 婚假：员工结婚享有3天婚假，晚婚（男25周岁/女23周岁以上）额外增加7天。
5. 产假：女性员工享有98天产假，难产增加15天，多胞胎每多一个增加15天。
6. 陪产假：男性员工配偶生育享有7天陪产假。

第三条 审批流程
员工请假1天以内由直属上级审批；1-3天由部门经理审批；3天以上由部门经理和HR联合审批。

第四条 薪资计算
年假、婚假、产假为带薪假；病假按基本工资的80%发放；事假为无薪假。
""",
        metadata={"source": "请假管理制度"}
    ),
    Document(
        page_content="""
公司报销管理制度（2025版）

第一条 总则
为规范公司费用报销管理，合理控制成本，特制定本制度。

第二条 报销范围
1. 差旅费：交通费、住宿费、餐饮补贴。住宿标准：一线城市不超过500元/晚，其他城市不超过350元/晚。
2. 业务招待费：需提前申请，单次不超过2000元，需注明招待对象和事由。
3. 办公用品：单次不超过500元，由部门统一采购。
4. 培训费：与工作相关的培训课程，需提前申请并获批准。
5. 交通费：因公外出产生的公共交通费用，需提供有效票据。

第三条 审批权限
单笔报销金额5000元以下由部门经理审批；5000元-20000元由部门总监审批；20000元以上由财务总监审批。

第四条 报销流程
员工在费用发生后10个工作日内提交报销申请，附原始票据。财务部门在5个工作日内完成审核和支付。

第五条 违规处理
虚假报销一经查实，除追回报销款外，给予警告处分；金额超过5000元的，予以解除劳动合同。
""",
        metadata={"source": "报销管理制度"}
    ),
    Document(
        page_content="""
会议室使用管理规定

第一条 会议室预约
员工可通过OA系统提前预约会议室，可预约时间段为工作日8:00-18:00。

第二条 使用规则
1. 每个预约时段为30分钟，单次预约不超过2小时。
2. 如需取消预约，需提前1小时操作。
3. 会议结束后请关闭投影、空调等设备，保持会议室整洁。
4. 超时使用将影响后续预约，需提前申请延长。

第三条 会议室资源
公司共有5间会议室：
- 创新厅（101室）：容量20人，配备投影仪、视频会议系统
- 协作厅（102室）：容量10人，配备白板、电视
- 专注厅（103室）：容量6人，配备白板
- 远见厅（201室）：容量30人，配备投影仪、视频会议系统、音响
- 灵感厅（202室）：容量4人，简约型小型会议室
""",
        metadata={"source": "会议室管理规定"}
    ),
    Document(
        page_content="""
智慧OA系统使用指南

智慧OA系统是公司全新升级的智能办公平台，集成了AI智能助手功能。
主要功能模块包括：

1. 请假管理：在线提交请假申请，查看审批进度
2. 报销管理：提交报销单，追踪报销状态
3. 会议室预定：查看会议室可用情况，在线预约
4. 公告管理：查看公司最新通知和公告
5. AI智能助手：智能问答、自动审批建议、异常检测

AI智能助手功能：
- 可通过自然语言查询请假、报销状态
- 可语音/文字创建申请
- 智能分析报销单异常情况
- 提供审批建议和风险评估
- 解答公司制度和流程问题

系统访问地址：http://oa.company.com
技术支持：IT运维部 ext.8888
""",
        metadata={"source": "OA系统使用指南"}
    ),
    Document(
        page_content="""
公司组织架构（2025年）

公司设以下部门：
1. 技术研发部：负责产品研发和技术创新，下设前端组、后端组、AI组、测试组
2. 产品设计部：负责产品规划和用户体验设计
3. 市场运营部：负责市场营销、品牌推广和用户运营
4. 人力资源部：负责招聘、培训、薪酬福利和员工关系
5. 财务部：负责公司财务管理、成本控制和报销审核
6. 行政管理部：负责办公环境、资产管理和行政支持

汇报关系：
员工 → 部门经理 → 部门总监 → VP → CEO
""",
        metadata={"source": "公司组织架构"}
    ),
]


def init_knowledge_base():
    try:
        if os.path.exists(PERSIST_DIR) and os.path.isdir(PERSIST_DIR) and os.listdir(PERSIST_DIR):
            return True

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""]
        )
        split_docs = text_splitter.split_documents(KNOWLEDGE_DOCS)

        embeddings = get_embeddings()
        Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings,
            persist_directory=PERSIST_DIR,
        )
        return True
    except Exception as e:
        import traceback
        print(f"知识库初始化失败: {e}")
        traceback.print_exc()
        return False


def search_knowledge(query: str, k: int = 5) -> List[Document]:
    try:
        embeddings = get_embeddings()
        vectorstore = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings,
        )
        return vectorstore.similarity_search(query, k=k)
    except Exception:
        return []


def rag_query(question: str) -> str:
    try:
        docs = search_knowledge(question, k=4)
        if not docs:
            return "抱歉，知识库暂时不可用，但您仍然可以咨询我关于公司政策的问题。例如：年假天数、病假审批流程、报销限额等。"

        context = "\n\n---\n\n".join([d.page_content for d in docs])

        llm = get_llm()
        prompt = f"""你是一个企业OA系统的知识助手。请根据以下参考资料回答用户的问题。
如果参考资料中没有相关信息，请如实告知。请用专业、清晰的语气回复。

参考资料：
{context}

用户问题：{question}

请回答："""

        response = llm.invoke([HumanMessage(content=prompt)])
        sources = set(d.metadata.get("source", "未知来源") for d in docs)
        return f"{response.content}\n\n📚 参考来源：{', '.join(sources)}"
    except Exception as e:
        return f"知识库查询失败: {str(e)}。您可以换个方式提问，或咨询公司基本政策。"
