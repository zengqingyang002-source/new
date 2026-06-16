"""
数据模型模块 - 定义所有数据库表的结构

这个文件里的每个类都对应数据库中的一张表。
新手理解要点：
- 每个类 = 一张数据库表
- 每个类属性 = 表中的一个字段（列）
- SQLAlchemy 会根据这些定义自动创建/更新表结构

简单类比：就像 Excel 表格的"表头设计"
- 类名 = 工作表名
- 属性名 = 列名
- 属性的类型 = 这列存什么数据（数字、文字、日期等）
"""

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base


class TimestampMixin:
    """
    时间戳混入类 —— 让其他表自动拥有 create_time 和 update_time 字段

    混入（Mixin）是一种代码复用技巧：
    其他类通过继承这个类，就能自动获得创建时间和更新时间字段，
    不需要每个类都重复定义。
    """
    create_time: Mapped[str] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[str] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class SysUser(Base, TimestampMixin):
    """
    系统用户表 —— 存储所有用户信息

    注意：这个表不只存"系统管理员"，而是存所有类型的用户：
    - 客户（CUSTOMER）：咨询留学信息的潜在客户
    - 学生（STUDENT）：已经报名的学生
    - 员工（EMPLOYEE）：公司的顾问、老师等
    - 管理员（ADMIN）：系统管理员
    """
    __tablename__ = "sys_user"  # 数据库中的表名

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # 用户名（唯一）
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)  # 加密后的密码
    real_name: Mapped[str] = mapped_column(String(64), nullable=False)  # 真实姓名
    user_type: Mapped[str] = mapped_column(String(32), nullable=False)  # 用户类型：CUSTOMER/STUDENT/EMPLOYEE
    employee_role: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 员工角色：ADMIN/EMPLOYEE（员工才有）
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)  # 所属部门
    contact_info: Mapped[str | None] = mapped_column(String(128), nullable=True)  # 联系方式
    status: Mapped[str] = mapped_column(String(32), default="正常")  # 用户状态：正常/禁用


class CrmLead(Base, TimestampMixin):
    """
    客户意向表（CRM Lead）—— 存储"意向客户"的信息

    Lead（销售线索）是销售流程中的第一步：
    客户来咨询 -> 成为 Lead（意向客户）-> 跟进 -> 签约 -> 成为正式学生

    这个表存的是"还没签约但有可能签约的潜在客户"的信息。
    """
    __tablename__ = "crm_lead"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_name: Mapped[str] = mapped_column(String(64), nullable=False)  # 客户姓名
    contact_info: Mapped[str | None] = mapped_column(String(128), nullable=True)  # 联系方式（电话/微信等）
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    education: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 学历：高中/本科/硕士等
    background_info: Mapped[str | None] = mapped_column(Text, nullable=True)  # 客户背景信息（自由文本）
    intended_project: Mapped[str | None] = mapped_column(String(128), nullable=True)  # 意向项目（新加坡/德国等）
    follow_up_history: Mapped[str | None] = mapped_column(Text, nullable=True)  # 跟进历史记录
    status: Mapped[str] = mapped_column(String(32), default="新增意向")  # 跟进状态：新增意向/跟进中/已签约/已流失
    owner_employee_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 负责跟进的员工 ID


class LeadEvaluation(Base):
    """
    客户评估记录表 —— 存储 AI 对客户的评估结果

    每次系统对客户进行"智能评估"后，都会在这里生成一条记录，
    内容包括：匹配的项目、评分、等级、销售建议等。
    """
    __tablename__ = "lead_evaluation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 关联的客户 ID（如果已保存到 CRM）
    source_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 信息来源：text/docx/pdf 等
    extracted_info: Mapped[str | None] = mapped_column(Text, nullable=True)  # 从文本中提取的客户信息（JSON 字符串）
    matched_project: Mapped[str | None] = mapped_column(String(128), nullable=True)  # 推荐匹配的项目
    singapore_score: Mapped[int] = mapped_column(Integer, default=0)  # 新加坡方向匹配分（0-100）
    germany_score: Mapped[int] = mapped_column(Integer, default=0)  # 德国方向匹配分（0-100）
    lead_level: Mapped[str] = mapped_column(String(8), default="C")  # 客户等级：A(80+)/B(60+)/C(<60)
    reasons: Mapped[str | None] = mapped_column(Text, nullable=True)  # 评分理由（JSON 数组字符串）
    missing_fields: Mapped[str | None] = mapped_column(Text, nullable=True)  # 缺失的字段信息（建议补充）
    suggested_questions: Mapped[str | None] = mapped_column(Text, nullable=True)  # 建议追问的问题
    sales_advice: Mapped[str | None] = mapped_column(Text, nullable=True)  # 销售建议
    create_time: Mapped[str] = mapped_column(DateTime, server_default=func.now())


class EmployeeDailyReport(Base):
    """
    员工日报表 —— 存储员工每天的工作汇报
    """
    __tablename__ = "employee_daily_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)  # 员工 ID
    report_date: Mapped[str] = mapped_column(Date, nullable=False)  # 汇报日期
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 日报正文内容
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI 生成的摘要建议
    create_time: Mapped[str] = mapped_column(DateTime, server_default=func.now())


class StudentAdminService(Base, TimestampMixin):
    """
    学生行政服务申请表 —— 存储学生提交的各种行政申请

    目前主要用于"请假申请"，但设计上可扩展到其他服务类型。
    """
    __tablename__ = "student_admin_service"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)  # 申请的学生 ID
    service_type: Mapped[str] = mapped_column(String(32), nullable=False)  # 服务类型：请假/调课/转班等
    start_time: Mapped[str | None] = mapped_column(DateTime, nullable=True)  # 开始时间
    end_time: Mapped[str | None] = mapped_column(DateTime, nullable=True)  # 结束时间
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)  # 申请原因
    status: Mapped[str] = mapped_column(String(32), default="待审批")  # 审批状态：待审批/已通过/已驳回
    approver_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 审批人 ID
    related_academic_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 关联的教务老师 ID


class StudentPsychProfile(Base):
    """
    学生心理档案表 —— 存储学生的心理健康状态信息

    用于跟踪学生的情绪变化，及时发现心理问题。
    """
    __tablename__ = "student_psych_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # 学生 ID（唯一，一个学生一条记录）
    latest_emotion_tag: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 最新情绪标签：焦虑/平静/开心等
    emotion_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 情绪评分
    last_interaction_time: Mapped[str | None] = mapped_column(DateTime, nullable=True)  # 最近一次交互时间
    emotion_history: Mapped[str | None] = mapped_column(Text, nullable=True)  # 情绪变化历史记录
    update_time: Mapped[str] = mapped_column(DateTime, server_default=func.now())


class StudentPsychAlert(Base):
    """
    学生心理预警表 —— 当学生的心理状态出现异常时，生成预警记录

    比如系统检测到学生多次提到"焦虑"、"失眠"等关键词时，
    会自动生成一条预警，提醒老师关注。
    """
    __tablename__ = "student_psych_alert"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)  # 预警学生 ID
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=False)  # 触发预警的原因（如：多次提到焦虑）
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)  # 风险等级：低/中/高
    status: Mapped[str] = mapped_column(String(32), default="未处理")  # 处理状态：未处理/跟进中/已解除
    teacher_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 负责处理的老师 ID
    create_time: Mapped[str] = mapped_column(DateTime, server_default=func.now())


class StudentFeedbackTicket(Base, TimestampMixin):
    """
    学生投诉/反馈工单表 —— 存储学生提交的投诉或反馈意见

    学生可以提交各种投诉或建议，老师负责处理和回复。
    """
    __tablename__ = "student_feedback_ticket"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)  # 提交反馈的学生 ID
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 投诉/反馈摘要
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # 详细描述
    status: Mapped[str] = mapped_column(String(32), default="待处理")  # 处理状态：待处理/处理中/已解决
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)  # 解决方案
    handler_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 处理人（员工 ID）
    is_notified: Mapped[int] = mapped_column(Integer, default=0)  # 是否已通知学生：0=未通知，1=已通知


class CourseProject(Base):
    """
    课程/项目表 —— 存储公司提供的所有留学项目信息

    比如：新加坡 2+2 国际本科班、中德精英人才共建计划等。
    """
    __tablename__ = "course_project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(String(128), nullable=False)  # 项目名称
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 项目分类：新加坡升学/德国双元制
    description: Mapped[str | None] = mapped_column(Text, nullable=True)  # 项目描述
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)  # 目标人群


class EventLecture(Base):
    """
    活动/讲座表 —— 存储公司举办的各种招生活动和讲座信息

    比如：线上项目说明会、校园开放日等。
    """
    __tablename__ = "event_lecture"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_name: Mapped[str] = mapped_column(String(128), nullable=False)  # 活动名称
    event_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 活动类型：线上/线下
    start_time: Mapped[str] = mapped_column(DateTime, nullable=False)  # 开始时间
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)  # 活动地点
    max_participants: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 最大参与人数
    current_participants: Mapped[int] = mapped_column(Integer, default=0)  # 当前已报名人数


class EventRegistration(Base):
    """
    活动报名表 —— 存储客户报名参加活动的记录
    """
    __tablename__ = "event_registration"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, nullable=False)  # 活动 ID
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False)  # 报名客户 ID
    status: Mapped[str] = mapped_column(String(32), default="已报名")  # 报名状态：已报名/已参加/已取消
    create_time: Mapped[str] = mapped_column(DateTime, server_default=func.now())


class StudentScore(Base):
    """
    学生成绩表 —— 存储学生的课程考试成绩
    """
    __tablename__ = "student_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)  # 学生 ID
    course_name: Mapped[str] = mapped_column(String(128), nullable=False)  # 课程名称
    score: Mapped[float] = mapped_column(Float, nullable=False)  # 成绩分数
    semester: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 学期
    create_time: Mapped[str] = mapped_column(DateTime, server_default=func.now())


class ReportSnapshot(Base):
    """
    报告快照表 —— 存储系统生成的各种报告的"快照"

    比如：客户经营分析报告、日报汇总、投诉周报等。
    生成报告时把内容存下来，以后可以随时查阅历史报告。
    """
    __tablename__ = "report_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(64), nullable=False)  # 报告类型：customer-analysis/daily-summary 等
    title: Mapped[str] = mapped_column(String(128), nullable=False)  # 报告标题
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 报告正文（Markdown 格式）
    source_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # 生成报告的原始数据（JSON 字符串）
    creator_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 创建人 ID
    create_time: Mapped[str] = mapped_column(DateTime, server_default=func.now())
