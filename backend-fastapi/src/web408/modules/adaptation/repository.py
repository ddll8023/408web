"""改编题查询的持久化边界。

Repository 只负责构造和执行改编题与来源引用查询，不负责事务提交、响应转换或业务校验。
"""
from dataclasses import dataclass
import json
from typing import Any

from sqlalchemy import and_, func, or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.models.enums import QuestionTypeEnum
from web408.modules.adaptation.models import AdaptationQuestion, AdaptationSource


@dataclass(frozen=True, slots=True)
class AdaptationQuery:
    """改编题分页查询的持久化参数，不依赖 HTTP Schema。"""

    page: int
    page_size: int
    subject_id: int | None
    category: str | None
    no_category: bool
    category_names: tuple[str, ...] | None
    sort_field: str
    sort_order: str
    question_type: QuestionTypeEnum | None = None
    keyword: str | None = None
    source_year: int | None = None
    source_question_number: int | None = None
    source_state: str = "all"


class AdaptationRepository:
    """封装改编题列表、来源引用和统计所需的数据库查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_paginated(
        self,
        params: AdaptationQuery,
    ) -> tuple[int, list[AdaptationQuestion]]:
        """按请求参数返回总数和当前页改编题。"""
        conditions = self._build_query_conditions(params)
        count_result = await self.session.exec(
            select(func.count())
            .select_from(AdaptationQuestion)
            .where(*conditions)
        )
        total = count_result.first() or 0

        order_column = {
            "id": AdaptationQuestion.id,
            "title": AdaptationQuestion.title,
            "update_time": AdaptationQuestion.update_time,
            "question_number": AdaptationQuestion.question_number,
            "create_time": AdaptationQuestion.create_time,
        }.get(params.sort_field, AdaptationQuestion.update_time)
        order_column = (
            order_column.asc()
            if params.sort_order == "asc"
            else order_column.desc()
        )
        offset = (params.page - 1) * params.page_size
        result = await self.session.exec(
            select(AdaptationQuestion)
            .where(*conditions)
            .order_by(order_column, AdaptationQuestion.id.asc())
            .offset(offset)
            .limit(params.page_size)
        )
        return total, result.all()

    async def get_by_id(self, question_id: int) -> AdaptationQuestion | None:
        """按主键查询改编题。"""
        result = await self.session.exec(
            select(AdaptationQuestion).where(AdaptationQuestion.id == question_id)
        )
        return result.first()

    async def list_by_ids(self, question_ids: set[int]) -> list[AdaptationQuestion]:
        """批量查询改编题，供来源反查拼装题目信息。"""
        if not question_ids:
            return []
        result = await self.session.exec(
            select(AdaptationQuestion).where(AdaptationQuestion.id.in_(question_ids))
        )
        return result.all()

    async def find_duplicate(
        self,
        title: str | None,
        question_number: int | None,
        exclude_id: int | None = None,
    ) -> AdaptationQuestion | None:
        """查询标题与题号组合是否已存在；两者任一为空时不参与唯一性判定。"""
        if title is None or question_number is None:
            return None
        conditions: list[Any] = [
            AdaptationQuestion.title == title,
            AdaptationQuestion.question_number == question_number,
        ]
        if exclude_id is not None:
            conditions.append(AdaptationQuestion.id != exclude_id)
        result = await self.session.exec(
            select(AdaptationQuestion).where(and_(*conditions))
        )
        return result.first()

    async def list_sources(self, adaptation_ids: set[int]) -> list[AdaptationSource]:
        """批量读取改编题的来源引用行。"""
        if not adaptation_ids:
            return []
        result = await self.session.exec(
            select(AdaptationSource)
            .where(AdaptationSource.adaptation_id.in_(adaptation_ids))
            .order_by(
                AdaptationSource.adaptation_id.asc(),
                AdaptationSource.source_year.asc(),
                AdaptationSource.source_question_number.asc(),
                AdaptationSource.id.asc(),
            )
        )
        return result.all()

    async def list_sources_by_keys(
        self,
        keys: set[tuple[int, int]],
        exclude_adaptation_id: int | None = None,
    ) -> list[AdaptationSource]:
        """按「年份 + 题号」读取来源行，供同源改编提示与反查使用。"""
        if not keys:
            return []
        conditions: list[Any] = [
            or_(
                *[
                    and_(
                        AdaptationSource.source_year == year,
                        AdaptationSource.source_question_number == number,
                    )
                    for year, number in sorted(keys)
                ]
            )
        ]
        if exclude_adaptation_id is not None:
            conditions.append(AdaptationSource.adaptation_id != exclude_adaptation_id)
        result = await self.session.exec(
            select(AdaptationSource)
            .where(*conditions)
            .order_by(AdaptationSource.source_year.asc(), AdaptationSource.id.asc())
        )
        return result.all()

    async def list_source_counts(
        self,
        years: set[int],
        subject_id: int | None = None,
    ) -> list[Any]:
        """按年份与题号统计被多少道改编题引用，同一改编题的不同小问只计一次。"""
        if not years:
            return []
        statement = select(
            AdaptationSource.source_year,
            AdaptationSource.source_question_number,
            func.count(func.distinct(AdaptationSource.adaptation_id)).label("count"),
        )
        if subject_id is not None:
            statement = statement.join(
                AdaptationQuestion,
                AdaptationQuestion.id == AdaptationSource.adaptation_id,
            )
        statement = statement.where(AdaptationSource.source_year.in_(years))
        if subject_id is not None:
            statement = statement.where(AdaptationQuestion.subject_id == subject_id)
        statement = statement.group_by(
            AdaptationSource.source_year,
            AdaptationSource.source_question_number,
        ).order_by(
            AdaptationSource.source_year.asc(),
            AdaptationSource.source_question_number.asc(),
        )
        result = await self.session.exec(statement)
        return result.all()

    async def list_category_values(self, subject_id: int) -> list[str | None]:
        """返回科目下改编题原始分类 JSON。"""
        result = await self.session.exec(
            select(AdaptationQuestion.category).where(
                and_(
                    AdaptationQuestion.subject_id == subject_id,
                    AdaptationQuestion.category.isnot(None),
                )
            )
        )
        return result.all()

    async def count_by_subject(self, subject_ids: set[int]) -> list[Any]:
        """批量统计指定科目的改编题数量，不读取目录模型。"""
        result = await self.session.exec(
            select(
                AdaptationQuestion.subject_id,
                func.count(AdaptationQuestion.id).label("count"),
            )
            .where(AdaptationQuestion.subject_id.in_(subject_ids))
            .group_by(AdaptationQuestion.subject_id)
        )
        return result.all()

    async def list_question_categories(self, subject_id: int) -> list[Any]:
        """读取科目下非空分类 JSON 和题目 ID，供目录统计使用。"""
        result = await self.session.exec(
            select(AdaptationQuestion.id, AdaptationQuestion.category).where(
                AdaptationQuestion.subject_id == subject_id,
                AdaptationQuestion.category.isnot(None),
                AdaptationQuestion.category != "",
            )
        )
        return result.all()

    async def count_questions_with_categories(self, subject_id: int) -> int:
        """统计非空分类字段的题目数，与真题、模拟题口径一致。"""
        result = await self.session.exec(
            select(func.count(func.distinct(AdaptationQuestion.id))).where(
                AdaptationQuestion.subject_id == subject_id,
                AdaptationQuestion.category.isnot(None),
                AdaptationQuestion.category != "",
            )
        )
        return result.one() or 0

    async def count_question_references(self, subject_id: int, category_name: str) -> int:
        """按原始分类名称统计引用，不去空白或展开子分类。"""
        result = await self.session.exec(
            select(func.count()).select_from(AdaptationQuestion).where(
                AdaptationQuestion.subject_id == subject_id,
                AdaptationQuestion.category.isnot(None),
                AdaptationQuestion.category.like(
                    self._json_category_like_pattern(category_name), escape="\\",
                ),
            )
        )
        return result.one() or 0

    async def list_by_category_tag(
        self,
        subject_id: int,
        category_name: str,
    ) -> list[AdaptationQuestion]:
        """返回科目下分类 JSON 含指定名称的改编题，供分类改名同步标签。"""
        result = await self.session.exec(
            select(AdaptationQuestion).where(
                AdaptationQuestion.subject_id == subject_id,
                AdaptationQuestion.category.isnot(None),
                AdaptationQuestion.category.like(
                    self._json_category_like_pattern(category_name), escape="\\",
                ),
            )
        )
        return result.all()

    async def list_image_reference_texts(self) -> list[Any]:
        """返回图片引用扫描所需的改编题文本字段。"""
        result = await self.session.exec(
            select(
                AdaptationQuestion.id,
                AdaptationQuestion.question_number,
                AdaptationQuestion.title,
                AdaptationQuestion.content,
                AdaptationQuestion.answer,
                AdaptationQuestion.options,
            )
        )
        return result.all()

    @staticmethod
    def _build_query_conditions(params: AdaptationQuery) -> list[Any]:
        """构造分页查询条件。"""
        conditions: list[Any] = []
        if params.subject_id is not None:
            conditions.append(AdaptationQuestion.subject_id == params.subject_id)

        if params.question_type is not None:
            conditions.append(AdaptationQuestion.question_type == params.question_type)

        if params.no_category is True:
            conditions.append(
                or_(
                    AdaptationQuestion.category.is_(None),
                    AdaptationQuestion.category == "",
                )
            )
        elif params.category_names is not None:
            conditions.extend(
                AdaptationRepository._category_conditions_for_names(
                    params.category_names
                )
            )
        else:
            conditions.extend(AdaptationRepository._category_conditions(params.category))

        if params.keyword and params.keyword.strip():
            keyword_pattern = f"%{params.keyword.strip()}%"
            conditions.append(
                or_(
                    AdaptationQuestion.title.ilike(keyword_pattern),
                    AdaptationQuestion.content.ilike(keyword_pattern),
                )
            )

        source_condition = AdaptationRepository._source_condition(params)
        if source_condition is not None:
            conditions.append(source_condition)
        return conditions

    @staticmethod
    def _source_condition(params: AdaptationQuery) -> Any | None:
        """按来源年份、题号或标注状态构造 EXISTS 条件。"""
        has_key_filter = (
            params.source_year is not None or params.source_question_number is not None
        )
        if not has_key_filter and params.source_state == "all":
            return None

        source_exists = select(AdaptationSource.id).where(
            AdaptationSource.adaptation_id == AdaptationQuestion.id
        )
        if params.source_year is not None:
            source_exists = source_exists.where(
                AdaptationSource.source_year == params.source_year
            )
        if params.source_question_number is not None:
            source_exists = source_exists.where(
                AdaptationSource.source_question_number == params.source_question_number
            )
        exists_clause = source_exists.exists()
        if params.source_state == "without_source":
            return ~exists_clause
        return exists_clause

    @staticmethod
    def _category_conditions(category: str | None) -> list[Any]:
        """构造单个 JSON 分类名称的兼容过滤条件。"""
        if not category or not category.strip():
            return []
        return AdaptationRepository._category_conditions_for_names((category.strip(),))

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
                AdaptationQuestion.category.isnot(None),
                AdaptationQuestion.category.like(
                    AdaptationRepository._json_category_like_pattern(name),
                    escape="\\",
                ),
            )
            for name in normalized_names
        ]
        if len(category_conditions) == 1:
            return category_conditions
        return [or_(*category_conditions)]

    @staticmethod
    def _json_category_like_pattern(category_name: str) -> str:
        """构造匹配 JSON 字符串元素的 LIKE 模式。"""
        serialized = json.dumps(category_name, ensure_ascii=False)
        escaped = serialized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return f"%{escaped}%"
