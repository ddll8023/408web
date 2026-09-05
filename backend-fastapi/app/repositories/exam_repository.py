"""真题查询的持久化边界。

Repository 只负责构造和执行真题查询，不负责事务提交、响应转换或业务校验。
"""
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import and_, case, func, or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.entities import ExamQuestion, Subject, User


@dataclass(frozen=True, slots=True)
class ExamQuery:
    """真题分页查询的持久化参数，不依赖 HTTP Schema。"""

    page: int
    page_size: int
    year: Optional[int]
    subject_id: Optional[int]
    category: Optional[str]
    no_category: bool
    keyword: Optional[str]
    sort_field: str
    sort_order: str
    category_names: Optional[tuple[str, ...]] = None


class ExamRepository:
    """封装真题列表、统计、索引和导出所需的数据库查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_paginated(
        self,
        params: ExamQuery,
    ) -> tuple[int, list[ExamQuestion]]:
        """按请求参数返回总数和当前页真题。"""
        conditions = self._build_query_conditions(params)
        count_result = await self.session.exec(
            select(func.count(ExamQuestion.id))
            .select_from(ExamQuestion)
            .where(*conditions)
        )
        total = count_result.first() or 0

        order_column = {
            "year": ExamQuestion.year,
            "update_time": ExamQuestion.update_time,
            "question_number": ExamQuestion.question_number,
        }.get(params.sort_field, ExamQuestion.update_time)
        order_column = (
            order_column.asc()
            if params.sort_order == "asc"
            else order_column.desc()
        )
        offset = (params.page - 1) * params.page_size
        result = await self.session.exec(
            select(ExamQuestion)
            .where(*conditions)
            .order_by(order_column)
            .offset(offset)
            .limit(params.page_size)
        )
        return total, result.all()

    async def get_by_id(self, question_id: int) -> Optional[ExamQuestion]:
        """按主键查询真题。"""
        result = await self.session.exec(
            select(ExamQuestion).where(ExamQuestion.id == question_id)
        )
        return result.first()

    async def find_duplicate(
        self,
        year: int,
        question_number: Optional[int],
        exclude_id: Optional[int] = None,
    ) -> Optional[ExamQuestion]:
        """查询指定年份和题号是否已存在真题。"""
        conditions: list[Any] = [
            ExamQuestion.year == year,
            ExamQuestion.question_number == question_number,
        ]
        if exclude_id is not None:
            conditions.append(ExamQuestion.id != exclude_id)
        result = await self.session.exec(
            select(ExamQuestion).where(and_(*conditions))
        )
        return result.first()

    async def get_year_stats(self, category: Optional[str] = None) -> list[Any]:
        """按年份聚合真题数量和选择题数量。"""
        conditions = self._category_conditions(category)
        result = await self.session.exec(
            select(
                ExamQuestion.year,
                func.count().label("count"),
                func.sum(
                    case(
                        (ExamQuestion.question_type == "CHOICE", 1),
                        else_=0,
                    )
                ).label("choice_count"),
            )
            .where(*conditions)
            .group_by(ExamQuestion.year)
            .order_by(ExamQuestion.year.desc())
        )
        return result.all()

    async def list_for_category_stats(
        self,
        subject_id: Optional[int] = None,
    ) -> list[ExamQuestion]:
        """返回用于内存展开分类统计的真题。"""
        conditions: list[Any] = [
            ExamQuestion.category.isnot(None),
            ExamQuestion.category != "",
        ]
        if subject_id:
            conditions.append(ExamQuestion.subject_id == subject_id)
        result = await self.session.exec(
            select(ExamQuestion).where(*conditions)
        )
        return result.all()

    async def get_subject(self, subject_id: int) -> Optional[Subject]:
        """按主键查询科目。"""
        result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        return result.first()

    async def get_author(self, author_id: int) -> Optional[User]:
        """按主键查询作者。"""
        result = await self.session.exec(select(User).where(User.id == author_id))
        return result.first()

    async def list_index_rows(self, subject_id: Optional[int] = None) -> list[Any]:
        """返回真题索引所需的轻量字段。"""
        conditions: list[Any] = []
        if subject_id:
            conditions.append(ExamQuestion.subject_id == subject_id)
        result = await self.session.exec(
            select(ExamQuestion.id, ExamQuestion.year, ExamQuestion.question_number)
            .where(*conditions)
            .order_by(ExamQuestion.year.desc(), ExamQuestion.question_number.asc())
        )
        return result.all()

    async def find_by_year(
        self,
        year: int,
        category: Optional[str] = None,
        subject_id: Optional[int] = None,
    ) -> list[ExamQuestion]:
        """按年份、分类和科目查询真题。"""
        conditions: list[Any] = [ExamQuestion.year == year]
        if subject_id:
            conditions.append(ExamQuestion.subject_id == subject_id)
        conditions.extend(self._category_conditions(category))
        result = await self.session.exec(
            select(ExamQuestion)
            .where(*conditions)
            .order_by(ExamQuestion.question_number)
        )
        return result.all()

    async def list_category_values(self, subject_id: int) -> list[Optional[str]]:
        """返回科目下真题原始分类 JSON。"""
        result = await self.session.exec(
            select(ExamQuestion.category).where(
                and_(
                    ExamQuestion.subject_id == subject_id,
                    ExamQuestion.category.isnot(None),
                )
            )
        )
        return result.all()

    async def find_all_for_index(
        self,
        category: Optional[str] = None,
    ) -> list[ExamQuestion]:
        """返回年份导航使用的真题列表。"""
        result = await self.session.exec(
            select(ExamQuestion)
            .where(*self._category_conditions(category))
            .order_by(ExamQuestion.year.desc(), ExamQuestion.question_number.asc())
        )
        return result.all()

    async def find_nav_rows(self, category: Optional[str] = None) -> list[Any]:
        """返回侧边栏导航所需的轻量字段。"""
        result = await self.session.exec(
            select(
                ExamQuestion.id,
                ExamQuestion.year,
                ExamQuestion.question_number,
                ExamQuestion.title,
                ExamQuestion.category,
            )
            .where(*self._category_conditions(category))
            .order_by(ExamQuestion.year.desc(), ExamQuestion.question_number.asc())
        )
        return result.all()

    async def find_by_subject_and_category(
        self,
        subject_id: Optional[int],
        category: str,
    ) -> list[ExamQuestion]:
        """按科目和分类查询真题。"""
        conditions: list[Any] = self._category_conditions(category)
        if subject_id:
            conditions.append(ExamQuestion.subject_id == subject_id)
        result = await self.session.exec(
            select(ExamQuestion)
            .where(*conditions)
            .order_by(ExamQuestion.year.desc(), ExamQuestion.question_number.asc())
        )
        return result.all()

    async def find_for_export(self, subject_id: int) -> list[ExamQuestion]:
        """返回指定科目全部真题，按年份和题号排序。"""
        result = await self.session.exec(
            select(ExamQuestion)
            .where(ExamQuestion.subject_id == subject_id)
            .order_by(ExamQuestion.year.desc(), ExamQuestion.question_number.asc())
        )
        return result.all()

    @staticmethod
    def _category_conditions(category: Optional[str]) -> list[Any]:
        """构造 JSON 分类名称的兼容过滤条件。"""
        if not category or not category.strip():
            return []
        return ExamRepository._category_conditions_for_names((category,))

    @staticmethod
    def _category_conditions_for_names(
        category_names: tuple[str, ...],
    ) -> list[Any]:
        """构造匹配多个分类名称的 JSON 过滤条件。"""
        normalized_names = tuple(
            dict.fromkeys(
                name for name in category_names if name and name.strip()
            )
        )
        if not normalized_names:
            return []

        category_conditions = [
            and_(
                ExamQuestion.category.isnot(None),
                ExamQuestion.category.like(f'%"{name}"%'),
            )
            for name in normalized_names
        ]
        if len(category_conditions) == 1:
            return category_conditions
        return [or_(*category_conditions)]

    @staticmethod
    def _build_query_conditions(params: ExamQuery) -> list[Any]:
        """构造分页查询条件。"""
        conditions: list[Any] = []
        if params.year is not None:
            conditions.append(ExamQuestion.year == params.year)
        if params.subject_id is not None:
            conditions.append(ExamQuestion.subject_id == params.subject_id)

        if params.no_category is True:
            conditions.append(
                or_(
                    ExamQuestion.category.is_(None),
                    ExamQuestion.category == "",
                )
            )
        else:
            if params.category_names is not None:
                conditions.extend(
                    ExamRepository._category_conditions_for_names(
                        params.category_names
                    )
                )
            else:
                conditions.extend(ExamRepository._category_conditions(params.category))

        if params.keyword and params.keyword.strip():
            keyword_pattern = f"%{params.keyword}%"
            conditions.append(
                or_(
                    ExamQuestion.title.ilike(keyword_pattern),
                    ExamQuestion.content.ilike(keyword_pattern),
                )
            )
        return conditions
