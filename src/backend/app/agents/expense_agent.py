import json
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from app.config import settings
from app.observability import metrics, TokenEstimator
from app.database import SessionLocal
from app.models import ExpenseReport


def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=temperature,
    )


def analyze_expenses(department: str = None) -> dict:
    db: Session = SessionLocal()
    try:
        query = db.query(ExpenseReport)
        if department:
            query = query.filter(ExpenseReport.department == department)
        expenses = query.order_by(ExpenseReport.created_at.desc()).limit(50).all()

        if not expenses:
            return {"summary": "没有找到报销数据", "anomalies": [], "suggestions": "无"}

        expense_data = []
        for e in expenses:
            expense_data.append({
                "id": e.id,
                "申请人": e.applicant,
                "部门": e.department,
                "类别": e.category,
                "金额": e.amount,
                "状态": e.status.value,
                "描述": e.description,
            })

        try:
            llm = get_llm(temperature=0.2)
            prompt = f"""你是一个企业财务分析专家。请分析以下报销数据，找出异常或值得关注的情况。

报销数据：
{json.dumps(expense_data, ensure_ascii=False, indent=2)}

请分析以下方面：
1. 是否有金额异常的报销单（同一类别下明显高于平均值的）
2. 是否有重复或相似的报销描述
3. 类别分布是否合理
4. 需要人工关注的风险点

输出JSON格式：
{{
    "summary": "总体分析摘要",
    "anomalies": [{{"id": 异常申请ID, "reason": "异常原因"}}],
    "risk_items": [{{"id": 风险申请ID, "reason": "风险原因"}}],
    "suggestions": "改进建议"
}}
"""
            response = llm.invoke([HumanMessage(content=prompt)])
            analysis = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        except Exception:
            analysis = {
                "summary": "AI分析暂时不可用",
                "anomalies": [],
                "risk_items": [],
                "suggestions": "请稍后重试",
            }

        for anomaly in analysis.get("anomalies", []):
            try:
                exp = db.query(ExpenseReport).filter(ExpenseReport.id == anomaly["id"]).first()
                if exp:
                    exp.anomaly_flag = True
                    exp.anomaly_reason = anomaly.get("reason", "")
            except Exception:
                pass
        db.commit()

        return analysis
    except Exception as e:
        return {"summary": f"分析失败: {str(e)}", "anomalies": [], "suggestions": "请稍后重试"}
    finally:
        db.close()


def detect_anomaly(expense_id: int) -> dict:
    db: Session = SessionLocal()
    try:
        expense = db.query(ExpenseReport).filter(ExpenseReport.id == expense_id).first()
        if not expense:
            return {"is_anomaly": False, "reason": "报销单不存在", "risk_level": "无"}

        all_expenses = db.query(ExpenseReport).filter(
            ExpenseReport.category == expense.category
        ).all()

        amounts = [e.amount for e in all_expenses if e.id != expense.id]
        avg_amount = sum(amounts) / len(amounts) if amounts else expense.amount

        try:
            llm = get_llm(temperature=0.1)
            prompt = f"""分析以下单笔报销单是否存在异常：

报销详情：
- ID: {expense.id}
- 申请人: {expense.applicant}
- 类别: {expense.category}
- 金额: {expense.amount}元
- 同类别平均金额: {avg_amount:.2f}元
- 描述: {expense.description}

判断该报销是否异常，输出JSON：
{{"is_anomaly": true/false, "reason": "判断理由", "risk_level": "低/中/高"}}
"""
            response = llm.invoke([HumanMessage(content=prompt)])
            return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        except Exception:
            is_abnormal = expense.amount > avg_amount * 2
            return {
                "is_anomaly": is_abnormal,
                "reason": f"金额{expense.amount}元，同类平均{avg_amount:.0f}元" if is_abnormal else "金额正常",
                "risk_level": "中" if is_abnormal else "低"
            }
    except Exception:
        return {"is_anomaly": False, "reason": "无法分析", "risk_level": "低"}
    finally:
        db.close()
