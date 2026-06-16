"""
数据库初始化模块 - 向数据库插入演示数据

这个模块负责在应用第一次启动时，往数据库里插入一些"演示数据"，
方便开发和测试。具体来说：
1. 创建 4 个测试用户（管理员、顾问、学生、客户）
2. 创建 3 个课程项目（新加坡升学、德国双元制等）
3. 创建 2 个意向客户
4. 创建一些测试用的请假申请、投诉工单、心理预警等
"""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    CourseProject,
    CrmLead,
    EmployeeDailyReport,
    EventLecture,
    ReportSnapshot,
    StudentAdminService,
    StudentFeedbackTicket,
    StudentPsychAlert,
    SysUser,
)


def init_demo_data(db: Session) -> None:
    """
    初始化演示数据

    如果数据库中已经有用户了（count() > 0），就跳过初始化，
    避免重复插入。这样可以保证多次重启服务不会插入重复数据。

    参数：
      db: 数据库会话对象，用来执行数据库操作
    """
    # 先检查是否已经有数据了，有就跳过
    if db.query(SysUser).count() > 0:
        return

    # ========== 1. 创建 4 个测试用户 ==========
    users = [
        SysUser(
            username="admin",
            password_hash=hash_password("123456"),  # 密码加密存储！
            real_name="管理员",
            user_type="EMPLOYEE",    # 员工类型
            employee_role="ADMIN",   # 管理员角色
            department="管理层",
            contact_info="admin@example.com",
        ),
        SysUser(
            username="employee",
            password_hash=hash_password("123456"),
            real_name="李顾问",
            user_type="EMPLOYEE",
            employee_role="EMPLOYEE",  # 普通员工
            department="国际教育事业部",
            contact_info="13800000001",
        ),
        SysUser(
            username="student",
            password_hash=hash_password("123456"),
            real_name="王同学",
            user_type="STUDENT",  # 学生类型
            department="新加坡项目班",
            contact_info="13800000002",
        ),
        SysUser(
            username="customer",
            password_hash=hash_password("123456"),
            real_name="张客户",
            user_type="CUSTOMER",  # 外部客户
            department="外部客户",
            contact_info="13800000003",
        ),
    ]
    db.add_all(users)  # add_all 可以批量添加多条记录
    db.flush()  # 刷新到数据库，这样 users 的 id 就生成了，后面可以引用

    # ========== 2. 创建 3 个课程项目 ==========
    projects = [
        CourseProject(
            project_name="新加坡 0.5/1+2 国际本科班",
            category="新加坡升学",
            description="面向高二在读、应往届高中毕业或中职中技同等学历学生，国内预科后赴新加坡完成本科。",
            target_audience="16-19 岁，高中或同等学历，有升学和留学意愿。",
        ),
        CourseProject(
            project_name="新加坡 2+2 国际本科班",
            category="新加坡升学",
            description="面向应往届初中毕业生，国内两年、新加坡两年，本科毕业。",
            target_audience="14-16 岁，初中毕业，有出国读本科意向。",
        ),
        CourseProject(
            project_name="中德精英人才共建计划",
            category="德国双元制",
            description="德国职业教育与企业实训结合，完成培训后可就业、升学并规划永居。",
            target_audience="18-35 岁，高中及以上学历，有德语学习意愿和职业发展需求。",
        ),
    ]
    db.add_all(projects)

    # ========== 3. 创建 2 个意向客户 ==========
    leads = [
        CrmLead(
            customer_name="张三",
            contact_info="1348907728",
            age=19,
            gender="男",
            education="高中",
            background_info="家庭经济条件较好，希望出国读本科，英语一般。",
            intended_project="新加坡国际本硕升学计划",
            follow_up_history="初次咨询，关注费用和学历认证。",
            status="跟进中",
            owner_employee_id=users[1].id,  # 分配给李顾问跟进
        ),
        CrmLead(
            customer_name="李四",
            contact_info="13900001111",
            age=24,
            gender="男",
            education="本科",
            background_info="想提升职业技能，关注德国就业和永居政策。",
            intended_project="中德精英人才共建计划",
            follow_up_history="已介绍德语 B1 要求。",
            status="新增意向",
            owner_employee_id=users[1].id,
        ),
    ]
    db.add_all(leads)

    # ========== 4. 创建测试用的请假申请、投诉、心理预警、日报、活动、报告 ==========
    db.add_all(
        [
            StudentAdminService(
                student_id=users[2].id,  # 王同学的请假申请
                service_type="请假",
                reason="因身体不适申请请假一天。",
                status="待审批",
                approver_id=users[1].id,
            ),
            StudentFeedbackTicket(
                student_id=users[2].id,
                content="签证材料反馈不够及时",
                detail="希望老师能告知目前材料审核进度。",
                status="处理中",
                handler_id=users[1].id,
            ),
            StudentPsychAlert(
                student_id=users[2].id,
                trigger_reason="最近多次提到焦虑和睡眠不好",
                risk_level="中",
                status="跟进中",
                teacher_id=users[1].id,
            ),
            EmployeeDailyReport(
                employee_id=users[1].id,
                report_date="2026-06-09",
                content="今日跟进新加坡项目客户 3 人，德国项目客户 1 人，完成 1 条投诉处理。",
                ai_summary="客户跟进正常，新加坡方向咨询量较高，需继续推动高意向客户转化。",
            ),
            EventLecture(
                event_name="新加坡升学项目线上说明会",
                event_type="线上",
                start_time="2026-06-15 19:30:00",
                location="腾讯会议",
                max_participants=80,
                current_participants=12,
            ),
            ReportSnapshot(
                report_type="customer-analysis",
                title="演示客户经营分析报告",
                content="当前系统内共有 2 名意向客户，新加坡方向 1 人，德国方向 1 人。建议优先跟进 A 类客户。",
                source_data="demo",
                creator_id=users[0].id,
            ),
        ]
    )

    # 最后提交所有更改到数据库
    db.commit()
