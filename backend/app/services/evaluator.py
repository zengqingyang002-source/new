"""
客户评估模块 —— 用规则引擎分析客户信息，给出匹配项目和评分

这个模块是整个系统的核心智能功能之一，它做的是"不用 AI 也能做 AI 的事"：
通过正则表达式（关键词匹配）和简单的打分规则，
分析客户提供的文字信息，判断他更适合"新加坡"还是"德国"的留学项目。

新手理解要点：
- 这个模块没有用真正的 AI，而是用"规则"（if-else 和关键词）
- 优点：速度快、逻辑透明、不依赖外部服务
- 类似一个"打分表"：满足条件就加分，最后看总分决定推荐什么
"""

import json
import re
from dataclasses import dataclass, asdict

# 常见的学历关键词列表（按优先级从低到高排列）
EDUCATION_KEYWORDS = [
    "初中",
    "高中",
    "中职",
    "中专",
    "技校",
    "大专",
    "专科",
    "本科",
    "硕士",
    "研究生",
]


@dataclass
class LeadEvaluationResult:
    """
    评估结果的数据类

    dataclass 是 Python 的一种"数据容器"，自动生成 __init__ 等方法。
    比普通类更简洁，适合用来传输数据。
    """
    extracted_info: dict           # 从客户文本中提取的结构化信息（姓名、年龄、学历等）
    matched_project: str           # 推荐匹配的项目名称
    singapore_score: int           # 新加坡方向得分（0-100）
    germany_score: int             # 德国方向得分（0-100）
    lead_level: str                # 客户等级：A(>=80分) / B(>=60分) / C(<60分)
    reasons: list[str]             # 评分理由
    missing_fields: list[str]      # 缺失的关键信息（建议补充）
    suggested_questions: list[str]  # 建议追问的问题
    sales_advice: str              # 销售跟进建议

    def to_dict(self) -> dict:
        """把对象转成普通字典，方便序列化为 JSON"""
        return asdict(self)


def extract_customer_info(text: str) -> dict:
    """
    从客户原始文本中提取结构化信息

    用正则表达式从一段文字中"挖出"：
    - 姓名、年龄、性别
    - 学历、手机号
    - 留学意向（提到了哪些关键词）
    - 语言基础（雅思、托福、德语等）
    - 家庭经济状况

    参数：
      text: 客户的原始文字（比如对话记录、填写的表单）

    返回一个字典，包含提取到的所有信息
    """
    # 把多个空格/换行合并成一个空格，方便正则匹配
    compact = re.sub(r"\s+", " ", text).strip()

    age = _extract_age(compact)
    education = _find_first(EDUCATION_KEYWORDS, compact)

    # 性别判断：谁最后出现就取谁
    gender = "男" if re.search(r"性别[:： ]*男|男", compact) else None
    if re.search(r"性别[:： ]*女|女", compact):
        gender = "女"

    name = _extract_name(compact)
    phone = _extract_phone(compact)

    # 留学意向关键词检测
    intentions: list[str] = []
    for keyword in ["留学", "出国", "本科", "硕士", "升学", "就业", "移民", "永居", "实习", "职业"]:
        if keyword in compact:
            intentions.append(keyword)

    # 语言能力关键词检测
    language: list[str] = []
    for keyword in ["英语", "雅思", "托福", "德语", "B1", "C1", "四级", "六级"]:
        if keyword in compact:
            language.append(keyword)

    # 经济状况判断
    economy = None
    if any(keyword in compact for keyword in ["有钱", "经济条件较好", "预算", "中等", "家庭支持"]):
        economy = "有一定经济基础或家庭支持"

    return {
        "name": name,
        "age": age,
        "gender": gender,
        "phone": phone,
        "education": education,
        "intentions": intentions,
        "language": language,
        "family_economy": economy,
        "raw_summary": compact[:600],  # 只保留前 600 个字符
    }


def evaluate_customer(text: str) -> LeadEvaluationResult:
    """
    评估客户的综合方法 —— 核心入口！

    流程：
    1. 提取客户信息
    2. 分别计算新加坡方向和德国方向的得分
    3. 比较两个方向的得分，决定推荐哪个项目
    4. 根据总分确定客户等级（A/B/C）
    5. 找出缺失的关键信息
    6. 生成建议追问的问题

    返回 LeadEvaluationResult 对象，包含所有评估结果。
    """
    info = extract_customer_info(text)
    singapore_score, sg_reasons = _score_singapore(info, text)
    germany_score, de_reasons = _score_germany(info, text)

    # 谁分高就推荐谁
    if singapore_score >= germany_score:
        matched_project = "新加坡国际本硕升学计划"
        score = singapore_score
        reasons = sg_reasons
        sales_advice = (
            "建议优先推荐新加坡国际本硕升学计划，重点介绍学制短、费用相对可控、学历认证、"
            "带薪实习和就业推荐等优势。"
        )
    else:
        matched_project = "中德精英人才共建计划"
        score = germany_score
        reasons = de_reasons
        sales_advice = (
            "建议优先推荐中德精英人才共建计划，重点介绍德国双元制、免学费、培训津贴、"
            "职业资格证书、就业和永居规划。"
        )

    # 客户等级：A >= 80分, B >= 60分, C < 60分
    lead_level = "A" if score >= 80 else "B" if score >= 60 else "C"

    # 分数太低就不推荐具体项目了
    if score < 45:
        matched_project = "暂不推荐，需补充信息后再判断"

    missing_fields = _missing_fields(info, text)
    suggested_questions = _suggest_questions(matched_project, missing_fields)

    return LeadEvaluationResult(
        extracted_info=info,
        matched_project=matched_project,
        singapore_score=singapore_score,
        germany_score=germany_score,
        lead_level=lead_level,
        reasons=reasons,
        missing_fields=missing_fields,
        suggested_questions=suggested_questions,
        sales_advice=sales_advice,
    )


def serialize_list(items: list[str]) -> str:
    """把列表转成 JSON 字符串（因为数据库存的字段是 Text 类型）"""
    return json.dumps(items, ensure_ascii=False)


def _extract_age(text: str) -> int | None:
    """
    从文本中提取年龄

    支持三种格式：
    - "年龄：20" 或 "年龄: 20"
    - "20 岁" 或 "20岁"
    - "出生日期：2000"（如果是出生年份，用 2026 - 年份 算出年龄）
    """
    patterns = [
        r"年龄[:： ]*(\d{1,2})",
        r"(\d{1,2})\s*岁",
        r"出生日期[:： ]*(19\d{2}|20\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        value = int(match.group(1))
        if value > 1900:  # 说明是出生年份，不是年龄
            return 2026 - value
        return value
    return None


def _extract_phone(text: str) -> str | None:
    """从文本中提取手机号（1 开头的 11 位数字）"""
    match = re.search(r"1[3-9]\d{9}", text)
    return match.group(0) if match else None


def _extract_name(text: str) -> str | None:
    """
    从文本中提取姓名

    支持格式：
    - "姓名：张三" 或 "姓名: 张三"
    - 文本开头的 2-4 个汉字后面跟空格
    """
    patterns = [
        r"姓名[:： ]*([一-龥]{2,4})",
        r"姓 名[:： ]*([一-龥]{2,4})",
        r"^([一-龥]{2,4})\s",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def _find_first(keywords: list[str], text: str) -> str | None:
    """
    在文本中查找第一个匹配的关键词

    用于从学历关键词列表中找出客户提到了哪个学历。
    EDUCATIOn_KEYWORDS 的顺序很重要：扫到第一个匹配就返回。
    """
    for keyword in keywords:
        if keyword in text:
            return keyword
    return None


def _score_singapore(info: dict, text: str) -> tuple[int, list[str]]:
    """
    计算"新加坡方向"的匹配分数（满分 100）

    打分规则（加分制）：
    + 年龄 14-25 岁：+25 分
    + 年龄 26-35 岁：+10 分（可考虑专升本）
    + 学历符合（初中到本科）：+25 分
    + 有升学/学历提升需求：+25 分
    + 有出国/英语意向：+15 分
    + 有经济/预算信息：+10 分

    返回（分数, 理由列表）
    """
    score = 0
    reasons: list[str] = []
    age = info.get("age")
    education = info.get("education")

    if age is not None:
        if 14 <= age <= 25:
            score += 25
            reasons.append(f"年龄 {age} 岁，符合新加坡项目主要招生年龄段。")
        elif 26 <= age <= 35:
            score += 10
            reasons.append(f"年龄 {age} 岁，可考虑专升本或本升硕路径。")
    if education in {"初中", "高中", "中职", "中专", "技校", "大专", "专科", "本科"}:
        score += 25
        reasons.append(f"学历为 {education}，可匹配新加坡升学或就业班项目。")
    if any(keyword in text for keyword in ["本科", "硕士", "升学", "学历", "名校", "专升本", "本升硕"]):
        score += 25
        reasons.append("客户存在明确升学或学历提升需求。")
    if any(keyword in text for keyword in ["新加坡", "英语", "雅思", "托福", "留学", "出国"]):
        score += 15
        reasons.append("客户信息中出现新加坡、英语或出国留学相关意向。")
    if any(keyword in text for keyword in ["有钱", "经济", "预算", "家庭", "费用"]):
        score += 10
        reasons.append("客户资料中体现了家庭经济或费用关注点，便于进一步确认预算。")
    return min(score, 100), reasons or ["资料较少，新加坡方向仍需补充年龄、学历、预算和升学意向。"]


def _score_germany(info: dict, text: str) -> tuple[int, list[str]]:
    """
    计算"德国方向"的匹配分数（满分 100）

    打分规则（加分制）：
    + 年龄 18-35 岁：+25 分
    + 学历高中及以上：+20 分
    + 有就业/职业技能需求：+25 分
    + 有德国/德语/永居意向：+20 分
    + 提到逻辑/动手/吃苦等关键词：+10 分

    返回（分数, 理由列表）
    """
    score = 0
    reasons: list[str] = []
    age = info.get("age")
    education = info.get("education")

    if age is not None and 18 <= age <= 35:
        score += 25
        reasons.append(f"年龄 {age} 岁，符合德国项目 18-35 岁要求。")
    if education in {"高中", "中职", "中专", "技校", "大专", "专科", "本科", "硕士", "研究生"}:
        score += 20
        reasons.append(f"学历为 {education}，符合德国项目高中及以上要求。")
    if any(keyword in text for keyword in ["就业", "职业", "技能", "实训", "动手", "工作"]):
        score += 25
        reasons.append("客户有就业、职业技能或实践培养相关需求。")
    if any(keyword in text for keyword in ["德国", "德语", "B1", "移民", "永居", "欧洲"]):
        score += 20
        reasons.append("客户信息中出现德国、德语、永居或欧洲发展意向。")
    if any(keyword in text for keyword in ["逻辑", "动手", "无犯罪", "吃苦", "封闭"]):
        score += 10
        reasons.append("客户资料体现了德国项目关注的能力或合规条件。")
    return min(score, 100), reasons or ["资料较少，德国方向仍需补充德语、就业意愿、无犯罪记录和培训接受度。"]


def _missing_fields(info: dict, text: str) -> list[str]:
    """
    找出缺失的关键信息

    这些信息对判断客户应该推荐什么项目很重要，
    如果缺失的话，顾问需要主动向客户询问。
    """
    missing: list[str] = []
    if not info.get("age"):
        missing.append("年龄")
    if not info.get("education"):
        missing.append("学历")
    if not info.get("phone"):
        missing.append("联系方式")
    if not info.get("family_economy"):
        missing.append("家庭经济或预算范围")
    if not info.get("language"):
        missing.append("语言基础")
    if "无犯罪" not in text:
        missing.append("是否无犯罪记录")
    return missing


def _suggest_questions(project: str, missing_fields: list[str]) -> list[str]:
    """
    根据缺失信息生成建议追问的问题

    如果客户缺了某些关键信息，顾问需要主动问客户。
    这个函数根据推荐的项目类型，生成有针对性的追问问题。
    最多返回 6 个问题。
    """
    questions = [f"请补充{field}。" for field in missing_fields[:3]]
    if "新加坡" in project:
        questions.extend(
            [
                "是否接受新加坡方向的本科或本硕连读路径？",
                "更倾向计算机、酒店运营、航空运营还是其他专业？",
                "家庭预算是否在 25-31 万元范围内？",
            ]
        )
    elif "德国" in project:
        questions.extend(
            [
                "是否愿意接受 6-12 个月德语封闭培训？",
                "是否有德语基础或学习计划？",
                "是否关注德国就业、升学或永居规划？",
            ]
        )
    else:
        questions.append("客户的目标国家、学历目标和预算范围分别是什么？")
    return questions[:6]
