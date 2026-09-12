"""分类查询的持久化边界。

Repository 只负责本模块分类和科目查询，不负责题库读取、树形业务规则或事务提交。
"""
from typing import Any

from sqlalchemy import func, text
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.catalog.models import ExamCategory, Subject


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
            conditions.append(ExamCategory.enabled.is_(True))
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
    ) -> ExamCategory | None:
        """按主键查询分类。"""
        statement = select(ExamCategory)
        if include_subject:
            statement = statement.options(selectinload(ExamCategory.subject))
        result = await self.session.exec(
            statement.where(ExamCategory.id == category_id)
        )
        return result.first()

    async def get_subject(self, subject_id: int) -> Subject | None:
        """按主键查询科目。"""
        result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        return result.first()

    async def list_subject_names(self, subject_ids: set[int]) -> list[Any]:
        """按科目 ID 批量读取科目名称。"""
        result = await self.session.exec(
            select(Subject.id, Subject.name).where(Subject.id.in_(subject_ids))
        )
        return result.all()

    async def list_subjects(self, *, order_by_name: bool = False) -> list[Subject]:
        """返回全部科目，默认按目录顺序，可选按名称排序。"""
        order_columns = (Subject.name,) if order_by_name else (Subject.order_num, Subject.id)
        result = await self.session.exec(
            select(Subject).order_by(*order_columns)
        )
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
            conditions.append(ExamCategory.enabled.is_(True))
        result = await self.session.exec(
            select(func.count())
            .select_from(ExamCategory)
            .where(*conditions)
        )
        return result.one() or 0

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

    async def list_category_scope_names(
        self,
        subject_id: int,
        category_name: str,
    ) -> list[str]:
        """返回启用分类节点及其全部启用子孙分类名称。"""
        categories = await self.list_by_subject(
            subject_id,
            enabled_only=True,
            include_subject=False,
        )
        selected = next(
            (category for category in categories if category.name == category_name),
            None,
        )
        if selected is None:
            # 兼容题目中仍存在、但目录中已不存在的历史分类标签。
            return [category_name]

        children_by_parent: dict[int | None, list[ExamCategory]] = {}
        for category in categories:
            children_by_parent.setdefault(category.parent_id, []).append(category)

        scope_names: list[str] = []
        pending = [selected]
        index = 0
        while index < len(pending):
            category = pending[index]
            index += 1
            scope_names.append(category.name)
            pending.extend(children_by_parent.get(category.id, []))

        return scope_names

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
        exclude_id: int | None = None,
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
        exclude_id: int | None = None,
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

    async def list_for_reorder(self, subject_id: int) -> list[ExamCategory]:
        """返回科目下全部分类，供移动操作重排。"""
        result = await self.session.exec(
            select(ExamCategory)
            .where(ExamCategory.subject_id == subject_id)
            .order_by(ExamCategory.order_num, ExamCategory.id)
        )
        return result.all()
