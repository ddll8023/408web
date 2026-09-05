"""分类查询的持久化边界。

Repository 只负责分类、科目和题目引用查询，不负责树形业务规则或事务提交。
"""
from typing import Any, Optional

from sqlalchemy import and_, func, text
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.entities import ExamCategory, ExamQuestion, MockQuestion, Subject


class CategoryRepository:
    """封装分类树、引用统计和分类管理所需的数据库查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def lock_structure(self) -> None:
        """在当前事务内请求分类表写锁。"""
        await self.session.exec(
            text("UPDATE exam_category SET order_num = order_num WHERE 0")
        )

    async def list_all(self) -> list[ExamCategory]:
        """按科目和顺序返回全部分类。"""
        result = await self.session.exec(
            select(ExamCategory)
            .options(selectinload(ExamCategory.subject))
            .order_by(
                ExamCategory.subject_id,
                ExamCategory.order_num,
                ExamCategory.id,
            )
        )
        return result.all()

    async def list_by_subject(
        self,
        subject_id: int,
        *,
        enabled_only: bool = False,
        include_subject: bool = True,
    ) -> list[ExamCategory]:
        """按科目返回分类，可选仅返回启用节点。"""
        conditions: list[Any] = [ExamCategory.subject_id == subject_id]
        if enabled_only:
            conditions.append(ExamCategory.enabled == True)
        statement = select(ExamCategory)
        if include_subject:
            statement = statement.options(selectinload(ExamCategory.subject))
        result = await self.session.exec(
            statement
            .where(*conditions)
            .order_by(ExamCategory.order_num, ExamCategory.id)
        )
        return result.all()

    async def get_by_id(
        self,
        category_id: int,
        *,
        include_subject: bool = False,
    ) -> Optional[ExamCategory]:
        """按主键查询分类。"""
        statement = select(ExamCategory)
        if include_subject:
            statement = statement.options(selectinload(ExamCategory.subject))
        result = await self.session.exec(
            statement.where(ExamCategory.id == category_id)
        )
        return result.first()

    async def get_subject(self, subject_id: int) -> Optional[Subject]:
        """按主键查询科目。"""
        result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        return result.first()

    async def list_subjects(self) -> list[Subject]:
        """返回全部科目。"""
        result = await self.session.exec(select(Subject))
        return result.all()

    async def count_categories(
        self,
        subject_id: int,
        *,
        enabled_only: bool = False,
    ) -> int:
        """统计科目下分类数量。"""
        conditions: list[Any] = [ExamCategory.subject_id == subject_id]
        if enabled_only:
            conditions.append(ExamCategory.enabled == True)
        result = await self.session.exec(
            select(func.count())
            .select_from(ExamCategory)
            .where(*conditions)
        )
        return result.one() or 0

    async def count_questions_with_categories(
        self,
        subject_id: int,
        question_type: str,
    ) -> int:
        """统计科目下带分类的去重题目数量。"""
        question_model = MockQuestion if question_type == "mock" else ExamQuestion
        result = await self.session.exec(
            select(func.count(func.distinct(question_model.id))).where(
                and_(
                    question_model.subject_id == subject_id,
                    question_model.category.isnot(None),
                )
            )
        )
        return result.one() or 0

    async def list_question_categories(
        self,
        subject_id: int,
        question_type: str,
    ) -> list[Any]:
        """返回题目 ID 与原始分类 JSON，供 Service 展开分类。"""
        question_model = MockQuestion if question_type == "mock" else ExamQuestion
        result = await self.session.exec(
            select(question_model.id, question_model.category).where(
                and_(
                    question_model.subject_id == subject_id,
                    question_model.category.isnot(None),
                )
            )
        )
        return result.all()

    async def list_descendants(self, category_id: int) -> set[int]:
        """迭代返回分类的全部子孙节点，避免递归查询。"""
        descendants: set[int] = set()
        frontier = {category_id}
        while frontier:
            result = await self.session.exec(
                select(ExamCategory.id).where(ExamCategory.parent_id.in_(frontier))
            )
            children = set(result.all()) - descendants
            descendants.update(children)
            frontier = children
        return descendants

    async def list_parents_for_subject(self, subject_id: int) -> list[ExamCategory]:
        """按顺序返回科目下所有候选父分类。"""
        result = await self.session.exec(
            select(ExamCategory)
            .options(selectinload(ExamCategory.subject))
            .where(ExamCategory.subject_id == subject_id)
            .order_by(ExamCategory.order_num, ExamCategory.id)
        )
        return result.all()

    async def count_children(self, category_id: int) -> int:
        """统计直接子分类数量。"""
        result = await self.session.exec(
            select(func.count())
            .select_from(ExamCategory)
            .where(ExamCategory.parent_id == category_id)
        )
        return result.one() or 0

    async def count_name_conflicts(
        self,
        subject_id: int,
        name: str,
        *,
        exclude_id: Optional[int] = None,
    ) -> int:
        """统计同科目下同名分类数量。"""
        conditions: list[Any] = [
            ExamCategory.subject_id == subject_id,
            ExamCategory.name == name,
        ]
        if exclude_id is not None:
            conditions.append(ExamCategory.id != exclude_id)
        result = await self.session.exec(
            select(func.count())
            .select_from(ExamCategory)
            .where(*conditions)
        )
        return result.one() or 0

    async def count_code_conflicts(
        self,
        subject_id: int,
        code: str,
        *,
        exclude_id: Optional[int] = None,
    ) -> int:
        """统计同科目下同编码分类数量。"""
        conditions: list[Any] = [
            ExamCategory.subject_id == subject_id,
            ExamCategory.code == code,
        ]
        if exclude_id is not None:
            conditions.append(ExamCategory.id != exclude_id)
        result = await self.session.exec(
            select(func.count())
            .select_from(ExamCategory)
            .where(*conditions)
        )
        return result.one() or 0

    async def count_question_references(
        self,
        subject_id: int,
        category_name: str,
        question_type: str,
    ) -> int:
        """统计题目 JSON 分类中对某分类名称的引用数量。"""
        question_model = MockQuestion if question_type == "mock" else ExamQuestion
        result = await self.session.exec(
            select(func.count())
            .select_from(question_model)
            .where(
                and_(
                    question_model.subject_id == subject_id,
                    question_model.category.isnot(None),
                    question_model.category.like(f'%"{category_name}"%'),
                )
            )
        )
        return result.one() or 0

    async def list_for_reorder(self, subject_id: int) -> list[ExamCategory]:
        """返回科目下全部分类，供移动操作重排。"""
        result = await self.session.exec(
            select(ExamCategory)
            .where(ExamCategory.subject_id == subject_id)
            .order_by(ExamCategory.order_num, ExamCategory.id)
        )
        return result.all()
