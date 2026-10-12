"""自定义分类查询的持久化边界。

Repository 只负责本模块分类和科目查询，不负责树形业务规则或事务提交。
"""
from typing import Any

from sqlalchemy import func, text
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.catalog.models import Subject
from web408.modules.custom_category.models import CustomCategory


class CustomCategoryRepository:
    """封装自定义分类树与数量统计所需的数据库查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def lock_structure(self) -> None:
        """在当前事务内请求自定义分类表写锁。"""
        await self.session.exec(
            text("UPDATE custom_category SET order_num = order_num WHERE 0")
        )

    async def list_by_subject(
        self,
        subject_id: int,
        *,
        enabled_only: bool = False,
        include_subject: bool = True,
    ) -> list[CustomCategory]:
        """按科目返回自定义分类，可选仅返回启用节点。"""
        conditions: list[Any] = [CustomCategory.subject_id == subject_id]
        if enabled_only:
            conditions.append(CustomCategory.enabled.is_(True))
        statement = select(CustomCategory)
        if include_subject:
            statement = statement.options(selectinload(CustomCategory.subject))
        result = await self.session.exec(
            statement
            .where(*conditions)
            .order_by(CustomCategory.order_num, CustomCategory.id)
        )
        return result.all()

    async def get_by_id(
        self,
        category_id: int,
        *,
        include_subject: bool = False,
    ) -> CustomCategory | None:
        """按主键查询自定义分类。"""
        statement = select(CustomCategory)
        if include_subject:
            statement = statement.options(selectinload(CustomCategory.subject))
        result = await self.session.exec(
            statement.where(CustomCategory.id == category_id)
        )
        return result.first()

    async def get_subject(self, subject_id: int) -> Subject | None:
        """按主键查询科目。"""
        result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        return result.first()

    async def list_subjects(self) -> list[Subject]:
        """返回全部科目，按目录顺序。"""
        result = await self.session.exec(
            select(Subject).order_by(Subject.order_num, Subject.id)
        )
        return result.all()

    async def count_categories(
        self,
        subject_id: int,
        *,
        enabled_only: bool = False,
    ) -> int:
        """统计科目下自定义分类数量。"""
        conditions: list[Any] = [CustomCategory.subject_id == subject_id]
        if enabled_only:
            conditions.append(CustomCategory.enabled.is_(True))
        result = await self.session.exec(
            select(func.count())
            .select_from(CustomCategory)
            .where(*conditions)
        )
        return result.one() or 0

    async def list_descendants(self, category_id: int) -> set[int]:
        """迭代返回自定义分类的全部子孙节点，避免递归查询。"""
        descendants: set[int] = set()
        frontier = {category_id}
        while frontier:
            result = await self.session.exec(
                select(CustomCategory.id).where(CustomCategory.parent_id.in_(frontier))
            )
            children = set(result.all()) - descendants
            descendants.update(children)
            frontier = children
        return descendants

    async def count_children(self, category_id: int) -> int:
        """统计直接子分类数量。"""
        result = await self.session.exec(
            select(func.count())
            .select_from(CustomCategory)
            .where(CustomCategory.parent_id == category_id)
        )
        return result.one() or 0

    async def count_name_conflicts(
        self,
        subject_id: int,
        name: str,
        *,
        exclude_id: int | None = None,
    ) -> int:
        """统计同科目下同名自定义分类数量。"""
        conditions: list[Any] = [
            CustomCategory.subject_id == subject_id,
            CustomCategory.name == name,
        ]
        if exclude_id is not None:
            conditions.append(CustomCategory.id != exclude_id)
        result = await self.session.exec(
            select(func.count())
            .select_from(CustomCategory)
            .where(*conditions)
        )
        return result.one() or 0

    async def count_code_conflicts(
        self,
        subject_id: int,
        code: str,
        *,
        exclude_id: int | None = None,
    ) -> int:
        """统计同科目下同编码自定义分类数量。"""
        conditions: list[Any] = [
            CustomCategory.subject_id == subject_id,
            CustomCategory.code == code,
        ]
        if exclude_id is not None:
            conditions.append(CustomCategory.id != exclude_id)
        result = await self.session.exec(
            select(func.count())
            .select_from(CustomCategory)
            .where(*conditions)
        )
        return result.one() or 0

    async def list_for_reorder(self, subject_id: int) -> list[CustomCategory]:
        """返回科目下全部自定义分类，供移动操作重排。"""
        result = await self.session.exec(
            select(CustomCategory)
            .where(CustomCategory.subject_id == subject_id)
            .order_by(CustomCategory.order_num, CustomCategory.id)
        )
        return result.all()
