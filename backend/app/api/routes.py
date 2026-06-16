"""
API 路由模块 —— 定义所有后端接口

这个文件是后端最核心的部分，定义了所有可以被前端调用的 API 接口。
新手理解要点：
- 每个函数就是一个 API 接口（比如 /api/auth/login 就是登录接口）
- 接口的"装饰器"（@router.get / @router.post 等）定义了：
  - HTTP 方法：GET（查）/ POST（增）/ PUT（改）/ DELETE（删）
  - 访问路径：浏览器请求的 URL
  - 响应格式：返回什么样的数据

简单类比：这个文件就像餐厅的"菜单"
- @router.get("/health") = 菜单上的"健康检查"这道菜
- @router.post("/auth/login") = "登录"这道菜
- 前端（Vue 页面）就是来"点菜"的客人
"""

import json
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_employee
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.session import get_db, ping_database
from app.models import (
    CourseProject,
    CrmLead,
    EmployeeDailyReport,
    EventLecture,
    LeadEvaluation,
    ReportSnapshot,
    StudentAdminService,
    StudentFeedbackTicket,
    StudentPsychAlert,
    SysUser,
)
from app.schemas import (
    ChatRequest,
    ChatResponse,
    DailyReportCreate,
    FeedbackCreate,
    FeedbackUpdate,
    LeadCreate,
    LeadEvaluationRequest,
    LeadStatusUpdate,
    LeaveApprove,
    LeaveCreate,
    LoginRequest,
    LoginResponse,
    ReportCreate,
)
from app.services.dify import (
    dify_client,
    fallback_customer_answer,
    fallback_employee_answer,
)
from app.services.evaluator import evaluate_customer, serialize_list
from app.services.file_parser import parse_upload
from app.services.reporting import save_report

# APIRouter 是 FastAPI 中用来组织路由的工具
# 这样可以把相关的接口放在一个文件里，主程序（main.py）只需引入这个 router
router = APIRouter()


def row_to_dict(row: Any) -> dict:
    """
    工具函数：把数据库行对象（SQLAlchemy Model）转换成普通字典

    因为数据库查出来的对象不能直接当 JSON 返回，
    这个函数遍历所有字段，把值取出来组装成一个普通的 Python 字典。

    特别处理了有个 isoformat() 方法的字段（如日期、时间），
    把它们转成字符串格式，方便序列化成 JSON。
    """
    data: dict[str, Any] = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        data[column.name] = value
    return data


# ==================== 系统接口 ====================

@router.get("/health")
def health() -> dict:
    """健康检查接口 —— 用来检测后端服务是否正常运行"""
    return {
        "app": settings.app_name,
        "env": settings.app_env,
        "database": ping_database(),          # 检查数据库连接是否正常
        "dify_base_url": settings.dify_base_url,
    }


# ==================== 认证相关接口 ====================

@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录接口

    流程：
    1. 根据用户名在数据库中查找用户
    2. 如果没找到或密码不匹配，返回 401 错误（未授权）
    3. 验证通过后，生成一个 Token（访问令牌）
    4. 返回 Token 和用户信息给前端

    注意：密码是加密后存储的，所以验证时也是加密后对比
    """
    user = db.query(SysUser).filter(SysUser.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.id, user.username, user.employee_role or user.user_type)
    return {"access_token": token, "user": user}


@router.get("/auth/me")
def me(user: SysUser = Depends(get_current_user)):
    """获取当前登录用户的信息"""
    return row_to_dict(user)


# ==================== 仪表盘接口 ====================

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: SysUser = Depends(get_current_user)):
    """
    仪表盘数据接口 —— 返回首页需要的各种统计数字

    统计内容包括：
    - 意向客户总数、已签约数
    - 待处理投诉数
    - 待审批请假数
    - 心理预警数
    - 客户意向项目分布（用于图表展示）
    """
    lead_count = db.query(CrmLead).count()
    signed_count = db.query(CrmLead).filter(CrmLead.status == "已签约").count()
    feedback_pending = db.query(StudentFeedbackTicket).filter(StudentFeedbackTicket.status != "已解决").count()
    leave_pending = db.query(StudentAdminService).filter(StudentAdminService.status == "待审批").count()
    psych_alerts = db.query(StudentPsychAlert).filter(StudentPsychAlert.status != "已解除").count()
    # 按意向项目分组统计客户数量
    project_rows = (
        db.query(CrmLead.intended_project, func.count(CrmLead.id))
        .group_by(CrmLead.intended_project)
        .all()
    )
    return {
        "metrics": {
            "leads": lead_count,
            "signed": signed_count,
            "pending_feedback": feedback_pending,
            "pending_leave": leave_pending,
            "psych_alerts": psych_alerts,
        },
        "project_distribution": [
            {"name": project or "未明确", "value": count} for project, count in project_rows
        ],
        "current_user": row_to_dict(user),
    }


# ==================== AI 聊天相关接口 ====================

@router.post("/chat/customer", response_model=ChatResponse)
async def customer_chat(payload: ChatRequest, user: SysUser = Depends(get_current_user)):
    """
    客户聊天接口 —— 供"客户"类型的用户与 AI 助手对话

    这个 AI 助手主要回答留学相关的问题（费用、项目、流程等）。

    流程：
    1. 调用 Dify AI 平台的聊天 API
    2. 如果 Dify 调用失败：
       - 如果没有开启"兜底模式"，直接报错
       - 如果开启了，用本地写好的"固定答案"来回复（fallback_* 函数）
    """
    try:
        raw = await dify_client.chat(
            settings.dify_customer_chat_api_key,
            payload.message,
            user=f"user-{user.id}",
            conversation_id=payload.conversation_id,
        )
        return {
            "answer": raw.get("answer", ""),
            "conversation_id": raw.get("conversation_id", payload.conversation_id),
            "source": "dify",
            "raw": raw,
        }
    except Exception as exc:
        if not settings.dify_fallback_enabled:
            raise HTTPException(status_code=502, detail=f"Dify 调用失败：{exc}") from exc
        return {
            "answer": fallback_customer_answer(payload.message),
            "conversation_id": payload.conversation_id,
            "source": "local-fallback",
            "raw": {"error": str(exc)},
        }


@router.post("/chat/employee", response_model=ChatResponse)
async def employee_chat(payload: ChatRequest, user: SysUser = Depends(require_employee)):
    """
    员工聊天接口 —— 供"员工"类型的用户与 AI 助手对话

    这个 AI 助手主要回答内部工作相关的问题（日报、投诉处理等）。
    注意：这个接口要求用户必须是员工类型（require_employee）
    """
    try:
        raw = await dify_client.chat(
            settings.dify_employee_chat_api_key,
            payload.message,
            user=f"user-{user.id}",
            conversation_id=payload.conversation_id,
        )
        return {
            "answer": raw.get("answer", ""),
            "conversation_id": raw.get("conversation_id", payload.conversation_id),
            "source": "dify",
            "raw": raw,
        }
    except Exception as exc:
        if not settings.dify_fallback_enabled:
            raise HTTPException(status_code=502, detail=f"Dify 调用失败：{exc}") from exc
        return {
            "answer": fallback_employee_answer(payload.message),
            "conversation_id": payload.conversation_id,
            "source": "local-fallback",
            "raw": {"error": str(exc)},
        }


# ==================== 客户评估相关接口 ====================

def save_evaluation(
    db: Session,
    result: dict,
    source_type: str,
    lead_id: int | None = None,
) -> LeadEvaluation:
    """
    工具函数：把 AI 评估结果保存到数据库

    参数：
      result: 评估结果字典（包含评分、匹配项目、销售建议等）
      source_type: 信息来源（text/docx/pdf 等）
      lead_id: 关联的客户 ID（如果是已经存到 CRM 的客户）
    """
    record = LeadEvaluation(
        lead_id=lead_id,
        source_type=source_type,
        extracted_info=json.dumps(result["extracted_info"], ensure_ascii=False),
        matched_project=result["matched_project"],
        singapore_score=result["singapore_score"],
        germany_score=result["germany_score"],
        lead_level=result["lead_level"],
        reasons=serialize_list(result["reasons"]),
        missing_fields=serialize_list(result["missing_fields"]),
        suggested_questions=serialize_list(result["suggested_questions"]),
        sales_advice=result["sales_advice"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/leads/evaluate")
async def evaluate_lead(
    payload: LeadEvaluationRequest,
    db: Session = Depends(get_db),
    user: SysUser = Depends(require_employee),
):
    """
    评估客户意向接口 —— 核心功能！

    这个接口做了两件事：
    1. 本地评估：用正则表达式规则快速分析客户文本，给出评分和推荐项目
    2. Dify 评估：同时调用 Dify AI 平台的工作流进行 AI 评估（非必须）

    如果 save_to_crm=True，还会自动创建一个客户记录（CrmLead）。

    评分维度：
    - 新加坡方向 0-100 分（看年龄、学历、留学意向等）
    - 德国方向 0-100 分（看年龄、学历、就业意向等）
    - 综合等级：A（>=80）/ B（>=60）/ C（<60）
    """
    # 1. 本地规则引擎评估
    local_result = evaluate_customer(payload.text).to_dict()

    # 2. 同时调用 Dify AI 平台评估（如果失败也不影响主流程）
    dify_raw = None
    try:
        dify_raw = await dify_client.workflow(
            settings.dify_lead_workflow_api_key,
            {"customer_text": payload.text},
            user=f"user-{user.id}",
        )
    except Exception as exc:
        dify_raw = {"error": str(exc), "mode": "local-fallback"}

    # 3. 可选：保存到 CRM
    lead_id = None
    if payload.save_to_crm:
        info = local_result["extracted_info"]
        lead = CrmLead(
            customer_name=info.get("name") or "未命名客户",
            contact_info=info.get("phone"),
            age=info.get("age"),
            gender=info.get("gender"),
            education=info.get("education"),
            background_info=payload.text[:1000],
            intended_project=local_result["matched_project"],
            follow_up_history="系统自动研判生成。",
            status="新增意向",
            owner_employee_id=user.id,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        lead_id = lead.id

    # 4. 保存评估记录
    record = save_evaluation(db, local_result, payload.source_type, lead_id=lead_id)
    return {"evaluation": local_result, "record": row_to_dict(record), "dify": dify_raw}


@router.post("/leads/upload")
async def upload_lead_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: SysUser = Depends(require_employee),
):
    """
    上传客户文件并评估接口

    支持上传文件格式：txt / docx / xlsx / pdf
    系统会自动解析文件内容，然后调用评估逻辑进行分析。

    流程：
    1. 接收上传的文件
    2. 解析文件内容（不同格式有不同的解析方式）
    3. 用同样的评估逻辑分析内容
    4. 返回评估结果
    """
    text, source_type = await parse_upload(file)
    result = evaluate_customer(text).to_dict()
    record = save_evaluation(db, result, source_type)
    return {
        "filename": file.filename,
        "source_type": source_type,
        "text_preview": text[:1200],
        "evaluation": result,
        "record": row_to_dict(record),
    }


# ==================== 客户管理（CRM）相关接口 ====================

@router.get("/leads")
def list_leads(db: Session = Depends(get_db), user: SysUser = Depends(require_employee)):
    """获取所有意向客户列表，按创建时间倒序排列（最新的在前）"""
    leads = db.query(CrmLead).order_by(desc(CrmLead.id)).all()
    return [row_to_dict(lead) for lead in leads]


@router.post("/leads")
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), user: SysUser = Depends(require_employee)):
    """手动创建新的意向客户"""
    lead = CrmLead(**payload.model_dump(), owner_employee_id=user.id)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return row_to_dict(lead)


@router.get("/leads/{lead_id}")
def get_lead(lead_id: int, db: Session = Depends(get_db), user: SysUser = Depends(require_employee)):
    """
    获取单个客户的详细信息

    同时返回该客户的所有历史评估记录（evaluations）
    """
    lead = db.get(CrmLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="客户不存在")
    # 查找该客户的所有评估记录
    evaluations = (
        db.query(LeadEvaluation)
        .filter(LeadEvaluation.lead_id == lead_id)
        .order_by(desc(LeadEvaluation.id))
        .all()
    )
    data = row_to_dict(lead)
    data["evaluations"] = [row_to_dict(item) for item in evaluations]
    return data


@router.put("/leads/{lead_id}/status")
def update_lead_status(
    lead_id: int,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(require_employee),
):
    """更新客户跟进状态（如：跟进中 -> 已签约）"""
    lead = db.get(CrmLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="客户不存在")
    lead.status = payload.status
    if payload.follow_up_note:
        old = lead.follow_up_history or ""
        lead.follow_up_history = f"{old}\n{payload.follow_up_note}".strip()
    db.commit()
    db.refresh(lead)
    return row_to_dict(lead)


# ==================== 课程项目接口 ====================

@router.get("/projects")
def list_projects(db: Session = Depends(get_db), user: SysUser = Depends(get_current_user)):
    """获取所有可报名的课程项目（新加坡升学、德国双元制等）"""
    return [row_to_dict(item) for item in db.query(CourseProject).all()]


# ==================== 活动讲座接口 ====================

@router.get("/events")
def list_events(db: Session = Depends(get_db), user: SysUser = Depends(get_current_user)):
    """获取所有活动/讲座信息，按开始时间排序"""
    return [row_to_dict(item) for item in db.query(EventLecture).order_by(EventLecture.start_time).all()]


# ==================== 员工日报接口 ====================

@router.post("/daily-reports")
def create_daily_report(
    payload: DailyReportCreate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(require_employee),
):
    """创建新的工作日报"""
    report = EmployeeDailyReport(
        employee_id=payload.employee_id or user.id,
        report_date=payload.report_date or date.today().isoformat(),
        content=payload.content,
        ai_summary=f"AI 摘要：{payload.content[:80]}。建议继续关注客户转化和服务响应。",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return row_to_dict(report)


@router.get("/daily-reports")
def list_daily_reports(db: Session = Depends(get_db), user: SysUser = Depends(require_employee)):
    """获取最近 50 条工作日报"""
    rows = db.query(EmployeeDailyReport).order_by(desc(EmployeeDailyReport.id)).limit(50).all()
    return [row_to_dict(row) for row in rows]


# ==================== 学生请假接口 ====================

@router.post("/student/leave")
def create_leave(payload: LeaveCreate, db: Session = Depends(get_db), user: SysUser = Depends(get_current_user)):
    """
    学生提交请假申请

    如果是学生用户，自动把当前用户设为请假人；
    如果是其他类型用户（如管理员代操作），默认使用 ID 为 3 的测试学生。
    """
    student_id = user.id if user.user_type == "STUDENT" else 3
    leave = StudentAdminService(
        student_id=student_id,
        service_type="请假",
        start_time=payload.start_time,
        end_time=payload.end_time,
        reason=payload.reason,
        status="待审批",
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return row_to_dict(leave)


@router.get("/student/leave")
def list_leave(db: Session = Depends(get_db), user: SysUser = Depends(get_current_user)):
    """
    获取请假申请列表

    如果是学生：只看自己的请假记录
    如果是员工/管理员：看所有人的请假记录
    """
    query = db.query(StudentAdminService).order_by(desc(StudentAdminService.id))
    if user.user_type == "STUDENT":
        query = query.filter(StudentAdminService.student_id == user.id)
    return [row_to_dict(row) for row in query.all()]


@router.put("/student/leave/{leave_id}/approve")
def approve_leave(
    leave_id: int,
    payload: LeaveApprove,
    db: Session = Depends(get_db),
    user: SysUser = Depends(require_employee),
):
    """员工审批请假申请（已通过 / 已驳回）"""
    leave = db.get(StudentAdminService, leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="请假申请不存在")
    leave.status = payload.status
    leave.approver_id = user.id
    db.commit()
    db.refresh(leave)
    return row_to_dict(leave)


# ==================== 学生投诉反馈接口 ====================

@router.post("/student/feedback")
def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db), user: SysUser = Depends(get_current_user)):
    """学生提交投诉/反馈"""
    student_id = user.id if user.user_type == "STUDENT" else 3
    ticket = StudentFeedbackTicket(
        student_id=student_id,
        content=payload.content,
        detail=payload.detail,
        status="待处理",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return row_to_dict(ticket)


@router.get("/student/feedback")
def list_feedback(db: Session = Depends(get_db), user: SysUser = Depends(get_current_user)):
    """
    获取投诉/反馈列表

    如果是学生：只看自己的
    如果是员工/管理员：看所有人的
    """
    query = db.query(StudentFeedbackTicket).order_by(desc(StudentFeedbackTicket.id))
    if user.user_type == "STUDENT":
        query = query.filter(StudentFeedbackTicket.student_id == user.id)
    return [row_to_dict(row) for row in query.all()]


@router.put("/student/feedback/{ticket_id}")
def update_feedback(
    ticket_id: int,
    payload: FeedbackUpdate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(require_employee),
):
    """员工处理投诉（更新处理状态和解决方案）"""
    ticket = db.get(StudentFeedbackTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="投诉工单不存在")
    ticket.status = payload.status
    ticket.solution = payload.solution
    ticket.handler_id = user.id
    ticket.is_notified = 1 if payload.status == "已解决" else ticket.is_notified
    db.commit()
    db.refresh(ticket)
    return row_to_dict(ticket)


# ==================== 学生心理预警接口 ====================

@router.get("/student/psych-alerts")
def list_psych_alerts(db: Session = Depends(get_db), user: SysUser = Depends(require_employee)):
    """获取所有心理预警记录"""
    rows = db.query(StudentPsychAlert).order_by(desc(StudentPsychAlert.id)).all()
    return [row_to_dict(row) for row in rows]


# ==================== 报告相关接口 ====================

@router.post("/reports")
async def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(require_employee),
):
    """
    生成报告接口

    流程：
    1. 先在本地根据数据库数据生成报告（本地逻辑）
    2. 同时调用 Dify AI 平台增强报告内容（非必须）
    3. 返回报告结果

    报告类型支持：
    - customer-analysis: 客户经营分析
    - daily-summary: 日报汇总
    - complaint-weekly: 投诉周报
    - psych-weekly: 心理健康周报
    """
    report = save_report(db, payload.report_type, creator_id=user.id)
    dify_raw = None
    try:
        dify_raw = await dify_client.workflow(
            settings.dify_report_workflow_api_key,
            {
                "report_type": payload.report_type,
                "local_report": report.content,
                "payload": payload.payload or {},
            },
            user=f"user-{user.id}",
        )
    except Exception as exc:
        dify_raw = {"error": str(exc), "mode": "local-fallback"}
    return {"report": row_to_dict(report), "dify": dify_raw}


@router.get("/reports")
def list_reports(db: Session = Depends(get_db), user: SysUser = Depends(require_employee)):
    """获取最近 50 条历史报告"""
    reports = db.query(ReportSnapshot).order_by(desc(ReportSnapshot.id)).limit(50).all()
    return [row_to_dict(report) for report in reports]
