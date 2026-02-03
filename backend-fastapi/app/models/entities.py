"""
数据模型定义模块
对应 Java 实体类与 create_tables.sql 表结构
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship, Column, JSON
from app.models.base import BaseModel
from app.models.enums import UserRoleEnum, QuestionTypeEnum, DifficultyEnum


# ====================================
# 用户表 (user)
# ====================================
class User(BaseModel, table=True):
    """用户模型"""
    __tablename__ = "user"

    username: str = Field(unique=True, index=True, description="用户名")
    password: str = Field(description="BCrypt加密密码")
    email: Optional[str] = Field(default=None, description="邮箱")
    role: str = Field(default=UserRoleEnum.USER.value, description="角色")
    enabled: bool = Field(default=True, description="账户启用状态")

    # 关系
    exam_questions: List["ExamQuestion"] = Relationship(back_populates="author")
    mock_questions: List["MockQuestion"] = Relationship(back_populates="author")
    resource_files: List["ResourceFile"] = Relationship(back_populates="uploader")
    knowledge_points: List["KnowledgePoint"] = Relationship(back_populates="author")


# ====================================
# 科目表 (subject)
# ====================================
class Subject(BaseModel, table=True):
    """科目模型"""
    __tablename__ = "subject"

    name: str = Field(unique=True, description="科目名称")
    code: str = Field(unique=True, description="科目编码")
    description: Optional[str] = Field(default=None, description="科目描述")
    order_num: int = Field(default=0, description="排序序号")
    enabled: bool = Field(default=True, description="是否启用")

    # 关系
    chapters: List["Chapter"] = Relationship(back_populates="subject", cascade_delete="all")
    exam_categories: List["ExamCategory"] = Relationship(back_populates="subject", cascade_delete="all")
    exam_questions: List["ExamQuestion"] = Relationship(back_populates="subject")
    mock_questions: List["MockQuestion"] = Relationship(back_populates="subject")


# ====================================
# 章节表 (chapter)
# ====================================
class Chapter(BaseModel, table=True):
    """章节模型"""
    __tablename__ = "chapter"

    subject_id: int = Field(foreign_key="subject.id", description="所属科目ID")
    parent_id: Optional[int] = Field(default=None, foreign_key="chapter.id", description="父章节ID")
    name: str = Field(description="章节名称")
    order_num: int = Field(default=0, description="排序序号")
    enabled: bool = Field(default=True, description="是否启用")

    # 关系
    subject: Optional[Subject] = Relationship(back_populates="chapters")
    parent: Optional["Chapter"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Chapter.id"}
    )
    children: List["Chapter"] = Relationship(back_populates="parent")
    knowledge_points: List["KnowledgePoint"] = Relationship()


# ====================================
# 分类标签表 (exam_category)
# ====================================
class ExamCategory(BaseModel, table=True):
    """分类标签模型"""
    __tablename__ = "exam_category"

    subject_id: int = Field(foreign_key="subject.id", description="所属科目ID")
    parent_id: Optional[int] = Field(default=None, foreign_key="exam_category.id", description="父分类ID")
    name: str = Field(description="分类名称")
    code: str = Field(description="分类编码")
    description: Optional[str] = Field(default=None, description="分类描述")
    order_num: int = Field(default=0, description="排序序号")
    enabled: bool = Field(default=True, description="是否启用")

    # 关系
    subject: Optional[Subject] = Relationship(back_populates="exam_categories")
    parent: Optional["ExamCategory"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "ExamCategory.id"}
    )
    children: List["ExamCategory"] = Relationship(back_populates="parent")


# ====================================
# 真题表 (exam_question)
# ====================================
class ExamQuestion(BaseModel, table=True):
    """真题模型"""
    __tablename__ = "exam_question"

    year: int = Field(description="年份")
    question_number: Optional[int] = Field(default=None, description="题号")
    question_type: str = Field(default=QuestionTypeEnum.ESSAY.value, description="题型")
    title: Optional[str] = Field(default=None, description="题目标题")
    content: str = Field(description="题目内容")
    options: Optional[str] = Field(default=None, description="选择题选项(JSON)")
    answer: Optional[str] = Field(default=None, description="答案")
    category: Optional[str] = Field(default=None, description="分类(JSON数组)")
    subject_id: Optional[int] = Field(default=None, foreign_key="subject.id", description="科目ID")
    difficulty: Optional[str] = Field(default=None, description="难度")
    author_id: int = Field(foreign_key="user.id", description="作者ID")

    # 关系
    subject: Optional[Subject] = Relationship(back_populates="exam_questions")
    author: Optional[User] = Relationship(back_populates="exam_questions")


# ====================================
# 模拟题表 (mock_question)
# ====================================
class MockQuestion(BaseModel, table=True):
    """模拟题模型"""
    __tablename__ = "mock_question"

    source: str = Field(description="来源机构")
    question_number: Optional[int] = Field(default=None, description="题号")
    question_type: str = Field(default=QuestionTypeEnum.ESSAY.value, description="题型")
    title: Optional[str] = Field(default=None, description="题目标题")
    content: str = Field(description="题目内容")
    options: Optional[str] = Field(default=None, description="选择题选项(JSON)")
    answer: Optional[str] = Field(default=None, description="答案")
    category: Optional[str] = Field(default=None, description="分类(JSON数组)")
    subject_id: Optional[int] = Field(default=None, foreign_key="subject.id", description="科目ID")
    difficulty: Optional[str] = Field(default=None, description="难度")
    author_id: int = Field(foreign_key="user.id", description="作者ID")

    # 关系
    subject: Optional[Subject] = Relationship(back_populates="mock_questions")
    author: Optional[User] = Relationship(back_populates="mock_questions")


# ====================================
# 资源文件表 (resource_file)
# ====================================
class ResourceFile(BaseModel, table=True):
    """资源文件模型"""
    __tablename__ = "resource_file"

    filename: str = Field(description="存储文件名")
    original_filename: str = Field(description="原始文件名")
    file_path: str = Field(description="文件存储路径")
    file_size: Optional[int] = Field(default=None, description="文件大小")
    file_type: Optional[str] = Field(default=None, description="文件类型")
    description: Optional[str] = Field(default=None, description="资源描述")
    download_count: int = Field(default=0, description="下载次数")
    uploader_id: int = Field(foreign_key="user.id", description="上传者ID")

    # 关系
    uploader: Optional[User] = Relationship(back_populates="resource_files")


# ====================================
# 随机出题统计表 (exam_random_stat)
# ====================================
class ExamRandomStat(BaseModel, table=True):
    """随机出题统计模型"""
    __tablename__ = "exam_random_stat"

    user_id: int = Field(unique=True, description="用户ID")
    total_attempts: int = Field(default=0, description="完成次数")
    last_attempt_time: datetime = Field(default_factory=datetime.utcnow, description="最近完成时间")


# ====================================
# 知识点表 (knowledge_point)
# ====================================
class KnowledgePoint(BaseModel, table=True):
    """知识点模型"""
    __tablename__ = "knowledge_point"

    title: str = Field(description="标题")
    category: str = Field(description="分类")
    chapter_id: Optional[int] = Field(default=None, foreign_key="chapter.id", description="章节ID")
    content: str = Field(description="Markdown格式内容")
    author_id: int = Field(foreign_key="user.id", description="作者ID")
    view_count: int = Field(default=0, description="浏览次数")
    create_time: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    update_time: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    # 关系
    chapter: Optional[Chapter] = Relationship()
    author: Optional[User] = Relationship()
