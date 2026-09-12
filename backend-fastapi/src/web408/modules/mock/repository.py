"""模拟题查询的持久化边界。

Repository 只负责构造和执行模拟题查询，不负责事务提交、响应转换或业务校验。
"""
from dataclasses import dataclass
import json
from typing import Any

from sqlalchemy import and_, func, or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.mock.models import MockQuestion


@dataclass(frozen=True, slots=True)
class MockQuery:
    """模拟题分页查询的持久化参数，不依赖 HTTP Schema。"""

    page: int
    page_size: int
    source: str | None
    category: str | None
    subject_id: int | None
    no_category: bool
    keyword: str | None
    sort_field: str
    sort_order: str
    category_names: tuple[str, ...] | None = None


class MockRepository:
    """封装模拟题列表、统计和索引所需的数据库查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_paginated(
        self,
        params: MockQuery,
    ) -> tuple[int, list[MockQuestion]]:
        """按请求参数返回总数和当前页模拟题。"""
        conditions = self._build_query_conditions(params)
        count_result = await self.session.exec(
            select(func.count())
            .select_from(MockQuestion)
            .where(*conditions)
        )
        total = count_result.first() or 0

        order_column = {
            "source": MockQuestion.source,
            "update_time": MockQuestion.update_time,
            "question_number": MockQuestion.question_number,
            "create_time": MockQuestion.create_time,
        }.get(params.sort_field, MockQuestion.update_time)
        order_column = (
            order_column.asc()
            if params.sort_order == "asc"
            else order_column.desc()
        )
        offset = (params.page - 1) * params.page_size
        result = await self.session.exec(
            select(MockQuestion)
            .where(*conditions)
            .order_by(order_column, MockQuestion.id.asc())
            .offset(offset)
            .limit(params.page_size)
        )
        return total, result.all()

    async def get_by_id(self, question_id: int) -> MockQuestion | None:
        """按主键查询模拟题。"""
        result = await self.session.exec(
            select(MockQuestion).where(MockQuestion.id == question_id)
        )
        return result.first()

    async def find_duplicate(
        self,
        source: str,
        title: str | None,
        question_number: int | None,
        exclude_id: int | None = None,
    ) -> MockQuestion | None:
        """查询来源、标题和题号是否已存在模拟题。"""
        conditions: list[Any] = [
            MockQuestion.source == source,
            MockQuestion.title == title,
            MockQuestion.question_number == question_number,
        ]
        if exclude_id is not None:
            conditions.append(MockQuestion.id != exclude_id)
        result = await self.session.exec(
            select(MockQuestion).where(and_(*conditions))
        )
        return result.first()

    async def get_source_stats(self, category: str | None = None) -> list[Any]:
        """按来源聚合模拟题数量。"""
        conditions: list[Any] = [MockQuestion.source.isnot(None)]
        conditions.extend(self._category_conditions(category))
        result = await self.session.exec(
            select(
                MockQuestion.source,
                func.count().label("count"),
            )
            .where(*conditions)
            .group_by(MockQuestion.source)
            .order_by(func.count().desc())
        )
        return result.all()

    async def get_sources(self) -> list[Any]:
        """按来源聚合题目数量并排序。"""
        result = await self.session.exec(
            select(
                MockQuestion.source,
                func.count().label("question_count"),
            )
            .group_by(MockQuestion.source)
            .order_by(MockQuestion.source)
        )
        return result.all()

    async def list_for_category_stats(self, subject_id: int) -> list[MockQuestion]:
        """返回用于内存展开分类统计的模拟题。"""
        result = await self.session.exec(
            select(MockQuestion).where(
                and_(
                    MockQuestion.subject_id == subject_id,
                    MockQuestion.category.isnot(None),
                    MockQuestion.category != "",
                )
            )
        )
        return result.all()

    async def find_by_source(
        self,
        source: str,
        category: str | None = None,
        subject_id: int | None = None,
    ) -> list[MockQuestion]:
        """按来源、分类和科目查询模拟题。"""
        conditions: list[Any] = [MockQuestion.source == source]
        if subject_id is not None:
            conditions.append(MockQuestion.subject_id == subject_id)
        conditions.extend(self._category_conditions(category))
        result = await self.session.exec(
            select(MockQuestion)
            .where(*conditions)
            .order_by(MockQuestion.question_number.asc(), MockQuestion.id.asc())
        )
        return result.all()

    async def list_category_values(self, subject_id: int) -> list[str | None]:
        """返回科目下模拟题原始分类 JSON。"""
        result = await self.session.exec(
            select(MockQuestion.category).where(
                and_(
                    MockQuestion.subject_id == subject_id,
                    MockQuestion.category.isnot(None),
                )
            )
        )
        return result.all()

    async def count_by_subject(self, subject_ids: set[int]) -> list[Any]:
        """批量统计指定科目的模拟题数量，不读取目录模型。"""
        result = await self.session.exec(
            select(MockQuestion.subject_id, func.count(MockQuestion.id).label("count"))
            .where(MockQuestion.subject_id.in_(subject_ids))
            .group_by(MockQuestion.subject_id)
        )
        return result.all()

    async def list_question_categories(self, subject_id: int) -> list[Any]:
        """读取科目下非空分类 JSON 和题目 ID，供目录统计使用。"""
        result = await self.session.exec(
            select(MockQuestion.id, MockQuestion.category).where(
                MockQuestion.subject_id == subject_id,
                MockQuestion.category.isnot(None),
                MockQuestion.category != "",
            )
        )
        return result.all()

    async def count_questions_with_categories(self, subject_id: int) -> int:
        """统计非空分类字段的题目数，保留历史 JSON 统计口径。"""
        result = await self.session.exec(
            select(func.count(func.distinct(MockQuestion.id))).where(
                MockQuestion.subject_id == subject_id,
                MockQuestion.category.isnot(None),
                MockQuestion.category != "",
            )
        )
        return result.one() or 0

    async def count_question_references(self, subject_id: int, category_name: str) -> int:
        """按原始分类名称统计引用，不去空白或展开子分类。"""
        result = await self.session.exec(
            select(func.count()).select_from(MockQuestion).where(
                MockQuestion.subject_id == subject_id,
                MockQuestion.category.isnot(None),
                MockQuestion.category.like(
                    self._json_category_like_pattern(category_name), escape="\\",
                ),
            )
        )
        return result.one() or 0

    async def get_titles_by_source(self, source: str) -> list[str | None]:
        """返回指定来源下去重后的标题。"""
        result = await self.session.exec(
            select(MockQuestion.title)
            .where(
                and_(
                    MockQuestion.source == source,
                    MockQuestion.title.isnot(None),
                )
            )
            .distinct()
            .order_by(MockQuestion.title)
        )
        return result.all()

    async def list_image_reference_texts(self) -> list[Any]:
        """返回图片引用扫描所需的模拟题文本字段。"""
        result = await self.session.exec(
            select(
                MockQuestion.id,
                MockQuestion.question_number,
                MockQuestion.title,
                MockQuestion.source,
                MockQuestion.content,
                MockQuestion.answer,
                MockQuestion.options,
            )
        )
        return result.all()

    @staticmethod
    def _category_conditions(category: str | None) -> list[Any]:
        """构造单个 JSON 分类名称的兼容过滤条件。"""
        if not category or not category.strip():
            return []
        return MockRepository._category_conditions_for_names((category.strip(),))

    @staticmethod
    def _category_conditions_for_names(
        category_names: tuple[str, ...],
    ) -> list[Any]:
        """构造匹配多个分类名称的 JSON 过滤条件。"""
        normalized_names = tuple(
            dict.fromkeys(
                name.strip() for name in category_names if name and name.strip()
            )
        )
        if not normalized_names:
            return []

        category_conditions = [
            and_(
                MockQuestion.category.isnot(None),
                MockQuestion.category.like(
                    MockRepository._json_category_like_pattern(name),
                    escape="\\",
                ),
            )
            for name in normalized_names
        ]
        if len(category_conditions) == 1:
            return category_conditions
        return [or_(*category_conditions)]

    @staticmethod
    def _build_query_conditions(params: MockQuery) -> list[Any]:
        """构造分页查询条件。"""
        conditions: list[Any] = []
        if params.source is not None:
            conditions.append(MockQuestion.source == params.source)
        if params.subject_id is not None:
            conditions.append(MockQuestion.subject_id == params.subject_id)

        if params.no_category is True:
            conditions.append(
                or_(
                    MockQuestion.category.is_(None),
                    MockQuestion.category == "",
                )
            )
        else:
            if params.category_names is not None:
                conditions.extend(
                    MockRepository._category_conditions_for_names(
                        params.category_names
                    )
                )
            else:
                conditions.extend(MockRepository._category_conditions(params.category))

        if params.keyword and params.keyword.strip():
            keyword_pattern = f"%{params.keyword.strip()}%"
            conditions.append(
                or_(
                    MockQuestion.title.ilike(keyword_pattern),
                    MockQuestion.content.ilike(keyword_pattern),
                )
            )
        return conditions

    @staticmethod
    def _json_category_like_pattern(category_name: str) -> str:
        """构造匹配 JSON 字符串元素的 LIKE 模式。"""
        serialized = json.dumps(category_name, ensure_ascii=False)
        escaped = serialized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return f"%{escaped}%"
