"""
报告生成模块 —— 根据数据库中的数据生成各种分析报告

这个模块提供"报告生成器"功能，支持 4 种类型的报告：
1. customer-analysis: 客户经营分析报告 —— 谁在咨询、状态如何、意向分布
2. daily-summary: 员工日报汇总 —— 汇总最近日记
3. complaint-weekly: 投诉处理周报 —— 投诉统计和改进建议
4. psych-weekly: 学生心理健康周报 —— 心理预警汇总

每种报告都从数据库统计真实数据，然后生成 Markdown 格式的文本。
"""

from collections import Counter
from sqlalchemy.orm import Session

from app.models import (
    CrmLead,
    EmployeeDailyReport,
    ReportSnapshot,
    StudentFeedbackTicket,
    StudentPsychAlert,
)


def build_report_content(db: Session, report_type: str) -> tuple[str, str, dict]:
    """
    根据报告类型构建报告内容

    参数：
      db: 数据库会话
      report_type: 报告类型

    返回：
      (报告标题, 报告内容（Markdown格式）, 原始数据)
    """
    if report_type == "customer-analysis":
        # 客户经营分析：统计所有客户的状态和意向项目分布
        leads = db.query(CrmLead).all()
        status_counter = Counter(lead.status for lead in leads)
        project_counter = Counter(lead.intended_project or "未明确" for lead in leads)
        content = [
            "## 全域客户经营分析报告",
            f"- 意向客户总数：{len(leads)}",
            f"- 客户状态分布：{dict(status_counter)}",
            f"- 意向项目分布：{dict(project_counter)}",
            "- 业务洞察：新加坡方向适合升学需求明确、预算可控的客户；德国方向适合就业、技能和海外长期发展诉求强的客户。",
            "- 建议动作：优先跟进 A/B 类客户，对缺失预算、语言基础和学历信息的客户进行二次追问。",
        ]
        return "全域客户经营分析报告", "\n".join(content), {
            "lead_count": len(leads),
            "status_counter": dict(status_counter),
            "project_counter": dict(project_counter),
        }

    if report_type == "daily-summary":
        # 日报汇总：提取最近的 20 条日报
        reports = db.query(EmployeeDailyReport).order_by(EmployeeDailyReport.id.desc()).limit(20).all()
        content = ["## 员工日报汇总报告"]
        for report in reports:
            content.append(f"- {report.report_date} 员工 {report.employee_id}：{report.ai_summary or report.content}")
        content.append("- 管理建议：关注高意向客户转化、投诉响应时效和重点项目咨询量。")
        return "员工日报汇总报告", "\n".join(content), {"report_count": len(reports)}

    if report_type == "complaint-weekly":
        # 投诉周报：分析所有投诉工单的状态分布
        tickets = db.query(StudentFeedbackTicket).all()
        status_counter = Counter(ticket.status for ticket in tickets)
        content = [
            "## 投诉处理周报",
            f"- 投诉总数：{len(tickets)}",
            f"- 处理状态分布：{dict(status_counter)}",
            "- 主要风险：长时间未处理投诉会影响学生体验和机构口碑。",
            "- 改进建议：设置 24 小时响应机制，并在处理完成后同步通知��生。",
        ]
        return "投诉处理周报", "\n".join(content), {"ticket_count": len(tickets), "status_counter": dict(status_counter)}

    if report_type == "psych-weekly":
        # 心理周报：分析心理预警的风险等级分布
        alerts = db.query(StudentPsychAlert).all()
        risk_counter = Counter(alert.risk_level for alert in alerts)
        content = [
            "## 学生心理健康周报",
            f"- 心理预警总数：{len(alerts)}",
            f"- 风险等级分布：{dict(risk_counter)}",
            "- 关注重点：焦虑、孤独感、睡眠问题和跨文化适应压力。",
            "- 建议动作：对中高风险学生安排顾问主动关怀，并记录跟进结果。",
        ]
        return "学生心理健康周报", "\n".join(content), {"alert_count": len(alerts), "risk_counter": dict(risk_counter)}

    # 不支持的报告类型
    return "智能报告", "暂不支持该报告类型，请选择客户经营、日报、投诉或心理周报。", {}


def save_report(db: Session, report_type: str, creator_id: int | None = None) -> ReportSnapshot:
    """
    生成报告并保存到数据库

    流程：
    1. 调用 build_report_content 生成报告内容
    2. 把报告保存到 ReportSnapshot 表（方便以后查看历史报告）
    3. 返回保存后的报告对象

    参数：
      db: 数据库会话
      report_type: 报告类型
      creator_id: 创建报告的员工 ID
    """
    import json

    title, content, source_data = build_report_content(db, report_type)
    report = ReportSnapshot(
        report_type=report_type,
        title=title,
        content=content,
        source_data=json.dumps(source_data, ensure_ascii=False),
        creator_id=creator_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
