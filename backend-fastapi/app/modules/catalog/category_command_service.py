"""分类写入用例。"""
from typing import List

from sqlalchemy.exc import OperationalError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.entities import ExamCategory
from app.modules.catalog.category_repository import CategoryRepository
from app.modules.catalog.schemas.category import (
    ExamCategoryCreateRequest,
    ExamCategoryMoveRequest,
    ExamCategoryResponse,
    ExamCategoryUpdateRequest,
)
from app.modules.catalog.category_code import (
    build_category_code,
    next_sibling_sequence,
    rebuild_subtree_codes,
    subject_code_prefix,
)
from app.modules.catalog.category_query_service import CategoryQueryService


class CategoryCommandService:
    """编排分类新增、编辑、移动和删除。"""

    def __init__(self, session: AsyncSession, query_service: CategoryQueryService) -> None:
        self.session = session
        self.repository = CategoryRepository(session)
        self.query_service = query_service

    async def _lock_structure(self) -> None:
        """在分类写用例内取得 SQLite 写锁。"""
        try:
            await self.repository.lock_structure()
        except OperationalError as exc:
            code = getattr(exc.orig, "sqlite_errorcode", 0) or 0
            if (code & 0xFF) in (5, 6):
                raise ConflictException("分类正在被修改，请刷新后重试") from exc
            raise

    async def create(self, request: ExamCategoryCreateRequest) -> ExamCategoryResponse:
        """创建分类并自动生成层级编码。"""
        await self._lock_structure()
        subject = await self.repository.get_subject(request.subject_id)
        if subject is None:
            raise NotFoundException("科目")

        categories = await self.repository.list_by_subject(
            request.subject_id,
            include_subject=False,
        )
        parent = None
        if request.parent_id is not None:
            parent = await self.repository.get_by_id(request.parent_id)
            if parent is None:
                raise NotFoundException(f"父分类不存在：ID={request.parent_id}")
            if parent.subject_id != request.subject_id:
                raise ConflictException("父分类不属于指定的科目")

        if await self.repository.count_name_conflicts(
            request.subject_id,
            request.name,
        ) > 0:
            raise ConflictException(f"分类名称已存在：{request.name}")

        code = build_category_code(
            subject_code_prefix(categories, subject.name),
            parent.code if parent else None,
            next_sibling_sequence(categories, request.parent_id),
            request.name,
        )
        if await self.repository.count_code_conflicts(
            request.subject_id,
            code,
        ) > 0:
            raise ConflictException("分类编码生成冲突，请刷新后重试")

        category = ExamCategory(
            subject_id=request.subject_id,
            parent_id=request.parent_id,
            name=request.name,
            code=code,
            description=request.description,
            order_num=request.order_num,
            enabled=request.enabled,
        )
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category, attribute_names=["subject"])
        response = self.query_service.to_response(category)
        await self.session.commit()
        return response

    async def update(
        self,
        category_id: int,
        request: ExamCategoryUpdateRequest,
    ) -> ExamCategoryResponse:
        """更新分类并提交事务。"""
        await self._lock_structure()
        category = await self.repository.get_by_id(
            category_id,
            include_subject=True,
        )
        if category is None:
            raise NotFoundException(f"分类不存在：ID={category_id}")

        update_data = request.model_dump(exclude_unset=True)
        subject_id = update_data.get("subject_id", category.subject_id)
        if subject_id is None:
            raise ValidationException("分类必须属于一个科目")
        if subject_id != category.subject_id:
            raise ConflictException("分类所属科目创建后不可修改")
        subject = await self.repository.get_subject(subject_id)
        if subject is None:
            raise NotFoundException("科目")

        parent_id = update_data.get("parent_id", category.parent_id)
        if parent_id is not None:
            if parent_id == category_id:
                raise ConflictException("不能将分类设置为自己的父分类")
            if parent_id in await self.query_service.get_descendant_ids(category_id):
                raise ConflictException("不能将分类移动到自己的子孙分类下")
            parent = await self.repository.get_by_id(parent_id)
            if parent is None:
                raise NotFoundException(f"父分类不存在：ID={parent_id}")
            if parent.subject_id != subject_id:
                raise ConflictException("父分类不属于指定的科目")

        if request.name is not None and request.name != category.name:
            if await self.repository.count_name_conflicts(
                subject_id,
                request.name,
                exclude_id=category_id,
            ) > 0:
                raise ConflictException(f"分类名称已被其他分类使用：{request.name}")
        old_parent_id = category.parent_id
        for field, value in update_data.items():
            setattr(category, field, value)

        if category.parent_id != old_parent_id:
            categories = await self.repository.list_for_reorder(subject_id)
            codes = rebuild_subtree_codes(
                categories,
                category_id,
                subject_code_prefix(categories, subject.name),
            )
            for item in categories:
                if item.id in codes:
                    item.code = codes[item.id]

        await self.session.flush()
        response = self.query_service.to_response(category)
        await self.session.commit()
        return response

    async def move(
        self,
        category_id: int,
        request: ExamCategoryMoveRequest,
    ) -> List[ExamCategoryResponse]:
        """原子移动整棵子树并重排同级节点。"""
        await self._lock_structure()
        category = await self.repository.get_by_id(category_id)
        if category is None:
            raise NotFoundException("分类")

        target = None
        if request.target_id is not None:
            target = await self.repository.get_by_id(request.target_id)
            if target is None:
                raise NotFoundException("目标分类")
            if target.subject_id != category.subject_id:
                raise ConflictException("不能跨科目移动分类")
            if target.id == category_id:
                raise ConflictException("不能将分类移动到自身")
            if target.id in await self.query_service.get_descendant_ids(category_id):
                raise ConflictException("不能将分类移动到自己的子孙分类中")

        old_parent_id = category.parent_id
        new_parent_id = (
            None
            if target is None
            else target.id if request.position == "inside" else target.parent_id
        )
        categories = await self.repository.list_for_reorder(category.subject_id)
        siblings = [
            item
            for item in categories
            if item.parent_id == new_parent_id and item.id != category_id
        ]
        index = len(siblings)
        if target is not None and request.position != "inside":
            index = next(i for i, item in enumerate(siblings) if item.id == target.id)
            if request.position == "after":
                index += 1
        siblings.insert(index, category)
        category.parent_id = new_parent_id
        for order_num, item in enumerate(siblings):
            item.order_num = order_num

        if old_parent_id != new_parent_id:
            old_siblings = [
                item
                for item in categories
                if item.parent_id == old_parent_id and item.id != category_id
            ]
            for order_num, item in enumerate(old_siblings):
                item.order_num = order_num

            subject = await self.repository.get_subject(category.subject_id)
            if subject is None:
                raise NotFoundException("科目")
            codes = rebuild_subtree_codes(
                categories,
                category_id,
                subject_code_prefix(categories, subject.name),
            )
            for item in categories:
                if item.id in codes:
                    item.code = codes[item.id]

        await self.session.flush()
        response = await self.query_service.get_categories_by_subject(category.subject_id)
        await self.session.commit()
        return response

    async def delete(self, category_id: int) -> None:
        """删除未被子分类或题目引用的分类。"""
        await self._lock_structure()
        category = await self.repository.get_by_id(category_id)
        if category is None:
            raise NotFoundException(f"分类不存在：ID={category_id}")
        if await self.repository.count_children(category_id) > 0:
            raise ConflictException("该分类存在子分类，无法删除")
        exam_count = await self.repository.count_question_references(
            category.subject_id,
            category.name,
            "exam",
        )
        if exam_count > 0:
            raise ConflictException(f"该分类被 {exam_count} 道真题引用，无法删除")
        mock_count = await self.repository.count_question_references(
            category.subject_id,
            category.name,
            "mock",
        )
        if mock_count > 0:
            raise ConflictException(f"该分类被 {mock_count} 道模拟题引用，无法删除")
        await self.session.delete(category)
        await self.session.commit()
