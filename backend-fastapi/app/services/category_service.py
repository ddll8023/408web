"""
分类管理服务模块
实现分类CRUD、树形结构和统计业务逻辑
"""
import logging
from typing import List, Optional
from collections import defaultdict
from sqlmodel import select, func, and_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.entities import ExamCategory, ExamQuestion, MockQuestion, Subject
from app.exception import NotFoundException, ConflictException
from app.schemas.category import (
    ExamCategoryCreateRequest,
    ExamCategoryUpdateRequest,
    ExamCategoryResponse,
    ExamCategoryTreeResponse,
    ExamCategoryStatResponse,
    ExamCategoryUsageResponse
)


# 获取服务日志记录器
logger = logging.getLogger(__name__)


class ExamCategoryService:
    """分类服务类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_categories(
        self,
        question_type: str = "exam"
    ) -> List[ExamCategoryResponse]:
        """
        查询所有分类（全局）

        Args:
            question_type: 题目类型（exam/mock）

        Returns:
            所有分类列表
        """
        logger.info("ExamCategoryService.get_all_categories started, question_type: %s", question_type)
        stmt = select(ExamCategory).order_by(ExamCategory.subject_id, ExamCategory.order_num)
        result = await self.session.exec(stmt)
        categories = result.all()

        responses = []
        for c in categories:
            response = self._to_response(c)
            # 填充题目统计
            if question_type == "mock":
                count = await self._count_mock_questions(c.subject_id, c.name)
            else:
                count = await self._count_exam_questions(c.subject_id, c.name)
            response.question_count = count
            responses.append(response)

        logger.info("ExamCategoryService.get_all_categories completed, count: %d", len(responses))
        return responses

    async def get_enabled_categories_by_subject(
        self,
        subject_id: int
    ) -> List[ExamCategoryResponse]:
        """
        根据科目ID查询启用的分类列表（用于前端选择器）

        Args:
            subject_id: 科目ID

        Returns:
            启用的分类列表（不带统计）
        """
        logger.info("ExamCategoryService.get_enabled_categories_by_subject started, subject_id: %d", subject_id)
        stmt = (
            select(ExamCategory)
            .where(
                and_(
                    ExamCategory.subject_id == subject_id,
                    ExamCategory.enabled == True
                )
            )
            .order_by(ExamCategory.order_num)
        )
        result = await self.session.exec(stmt)
        categories = result.all()

        logger.info("ExamCategoryService.get_enabled_categories_by_subject completed, count: %d", len(categories))
        return [self._to_response(c) for c in categories]

    async def get_categories_by_subject(
        self,
        subject_id: int,
        enabled_only: bool = False,
        question_type: str = "exam"
    ) -> List[ExamCategoryResponse]:
        """
        根据科目ID查询分类列表

        Args:
            subject_id: 科目ID
            enabled_only: 是否仅查询启用的分类
            question_type: 题目类型（exam/mock）

        Returns:
            分类列表（扁平，带统计）
        """
        logger.info("ExamCategoryService.get_categories_by_subject started, subject_id: %d, enabled_only: %s",
                    subject_id, enabled_only)
        conditions = [ExamCategory.subject_id == subject_id]
        if enabled_only:
            conditions.append(ExamCategory.enabled == True)

        stmt = select(ExamCategory).where(*conditions).order_by(ExamCategory.order_num)
        result = await self.session.exec(stmt)
        categories = result.all()

        # 转换为响应对象并填充统计
        responses = []
        for c in categories:
            response = self._to_response(c)

            # 填充题目统计
            if question_type == "mock":
                count = await self._count_mock_questions(subject_id, c.name)
            else:
                count = await self._count_exam_questions(subject_id, c.name)
            response.question_count = count

            responses.append(response)

        logger.info("ExamCategoryService.get_categories_by_subject completed, count: %d", len(responses))
        return responses

    async def get_category_tree(
        self,
        subject_id: int,
        enabled_only: bool = False,
        question_type: str = "exam"
    ) -> List[ExamCategoryTreeResponse]:
        """
        查询分类树形结构

        支持任意层级深度的树形结构构建。

        Args:
            subject_id: 科目ID
            enabled_only: 是否仅查询启用的分类
            question_type: 题目类型（exam/mock）

        Returns:
            分类树形结构列表
        """
        logger.info("ExamCategoryService.get_category_tree started, subject_id: %d, enabled_only: %s",
                    subject_id, enabled_only)

        # 第一步：查询所有分类
        categories = await self.get_categories_by_subject(
            subject_id, enabled_only, question_type
        )

        if not categories:
            logger.info("ExamCategoryService.get_category_tree completed, tree is empty")
            return []

        # 第二步：构建树形结构
        tree = self._build_tree(categories)

        logger.info("ExamCategoryService.get_category_tree completed, tree_nodes: %d", len(tree))
        return tree

    async def get_enabled_category_tree_with_stats(
        self,
        subject_id: int,
        question_type: str = "exam"
    ) -> List[ExamCategoryTreeResponse]:
        """
        获取启用的分类树（带统计，自动过滤空分类）

        Args:
            subject_id: 科目ID
            question_type: 题目类型（exam/mock）

        Returns:
            过滤后的分类树（不含空分类）
        """
        logger.info("ExamCategoryService.get_enabled_category_tree_with_stats started, subject_id: %d", subject_id)

        # 第一步：获取所有启用的分类
        categories = await self.get_categories_by_subject(
            subject_id, enabled_only=True, question_type=question_type
        )

        if not categories:
            logger.info("ExamCategoryService.get_enabled_category_tree_with_stats completed, tree is empty")
            return []

        # 第二步：构建树形结构
        tree = self._build_tree(categories)

        # 第三步：过滤空分类
        filtered_tree = self._filter_empty_categories(tree)

        logger.info("ExamCategoryService.get_enabled_category_tree_with_stats completed, tree_nodes: %d",
                    len(filtered_tree))
        return filtered_tree

    def _build_tree(
        self,
        categories: List[ExamCategoryResponse]
    ) -> List[ExamCategoryTreeResponse]:
        """
        构建分类树形结构（递归算法）

        支持任意层级深度。

        Args:
            categories: 扁平分类列表

        Returns:
            树形结构列表
        """
        # 1. 转换为树形VO对象，初始化children为空列表
        category_map: dict[int, ExamCategoryTreeResponse] = {}
        for c in categories:
            category_map[c.id] = ExamCategoryTreeResponse(
                id=c.id,
                subject_id=c.subject_id,
                subject_name=c.subject_name,
                parent_id=c.parent_id,
                parent_name=c.parent_name,
                name=c.name,
                code=c.code,
                description=c.description,
                order_num=c.order_num,
                enabled=c.enabled,
                question_count=c.question_count,
                children=[]
            )

        # 2. 按父ID分组，构建子节点映射
        children_map: dict[Optional[int], List[ExamCategoryTreeResponse]] = defaultdict(list)
        for category in category_map.values():
            children_map[category.parent_id].append(category)

        # 3. 递归构建树形结构
        tree: List[ExamCategoryTreeResponse] = []
        for category in category_map.values():
            if category.parent_id is None:
                # 顶级分类：递归设置子分类
                self._build_children_recursively(category, children_map)
                tree.append(category)

        # 4. 按order_num排序
        tree.sort(key=lambda x: x.order_num)
        for category in tree:
            if category.children:
                category.children.sort(key=lambda x: x.order_num)

        return tree

    def _build_children_recursively(
        self,
        parent: ExamCategoryTreeResponse,
        children_map: dict[Optional[int], List[ExamCategoryTreeResponse]]
    ) -> None:
        """
        递归构建子分类

        Args:
            parent: 父分类
            children_map: 子分类映射
        """
        children = children_map.get(parent.id, [])
        if children:
            for child in children:
                self._build_children_recursively(child, children_map)
            parent.children = children
        else:
            parent.children = []

    def _filter_empty_categories(
        self,
        categories: List[ExamCategoryTreeResponse]
    ) -> List[ExamCategoryTreeResponse]:
        """
        递归过滤题目数为0的分类

        规则：
        1. 叶子节点（无子分类）：直接根据 questionCount 判断
        2. 父节点：如果自身有题目或者有至少一个非空子分类，则保留

        Args:
            categories: 分类树

        Returns:
            过滤后的分类树
        """
        if not categories:
            return categories

        result: List[ExamCategoryTreeResponse] = []
        for category in categories:
            # 1. 先递归处理子分类
            if category.children:
                filtered_children = self._filter_empty_categories(category.children)
                category.children = filtered_children if filtered_children else []

            # 2. 判断是否保留该分类
            self_count = category.question_count or 0
            has_non_empty_children = bool(category.children)

            # 如果自身有题目或者有非空子分类，则保留
            if self_count > 0 or has_non_empty_children:
                result.append(category)

        return result

    async def get_category_stats(
        self,
        subject_id: Optional[int] = None,
        question_type: str = "exam"
    ) -> ExamCategoryStatResponse:
        """
        获取分类统计信息

        Args:
            subject_id: 科目ID（可选，None表示全局）
            question_type: 题目类型

        Returns:
            统计信息
        """
        logger.info("ExamCategoryService.get_category_stats started, subject_id: %s, question_type: %s",
                    subject_id, question_type)

        # 统计分类数量
        if subject_id:
            total_result = await self.session.exec(
                select(func.count()).select_from(ExamCategory).where(
                    ExamCategory.subject_id == subject_id
                )
            )
            enabled_result = await self.session.exec(
                select(func.count()).select_from(ExamCategory).where(
                    and_(
                        ExamCategory.subject_id == subject_id,
                        ExamCategory.enabled == True
                    )
                )
            )
        else:
            total_result = await self.session.exec(
                select(func.count()).select_from(ExamCategory)
            )
            enabled_result = await self.session.exec(
                select(func.count()).select_from(ExamCategory).where(
                    ExamCategory.enabled == True
                )
            )

        # 统计题目数量（去重）
        if question_type == "mock":
            if subject_id:
                question_result = await self.session.exec(
                    select(func.count(func.distinct(MockQuestion.id))).where(
                        and_(
                            MockQuestion.subject_id == subject_id,
                            MockQuestion.category.isnot(None)
                        )
                    )
                )
            else:
                question_result = await self.session.exec(
                    select(func.count(func.distinct(MockQuestion.id))).where(
                        MockQuestion.category.isnot(None)
                    )
                )
        else:
            if subject_id:
                question_result = await self.session.exec(
                    select(func.count(func.distinct(ExamQuestion.id))).where(
                        and_(
                            ExamQuestion.subject_id == subject_id,
                            ExamQuestion.category.isnot(None)
                        )
                    )
                )
            else:
                question_result = await self.session.exec(
                    select(func.count(func.distinct(ExamQuestion.id))).where(
                        ExamQuestion.category.isnot(None)
                    )
                )

        total_categories = total_result.one() or 0
        enabled_categories = enabled_result.one() or 0
        total_questions = question_result.one() or 0

        logger.info("ExamCategoryService.get_category_stats completed, total_categories: %d, "
                    "enabled_categories: %d, total_questions: %d",
                    total_categories, enabled_categories, total_questions)

        return ExamCategoryStatResponse(
            total_categories=total_categories,
            enabled_categories=enabled_categories,
            question_type=question_type,
            total_questions=total_questions
        )

    async def get_available_parent_categories(
        self,
        subject_id: int,
        exclude_id: Optional[int] = None
    ) -> List[ExamCategoryResponse]:
        """
        查询可作为父分类的列表（顶级分类，排除自身及其子孙）

        Args:
            subject_id: 科目ID
            exclude_id: 排除的分类ID

        Returns:
            可作为父分类的列表
        """
        # 获取所有启用的分类
        stmt = (
            select(ExamCategory)
            .where(
                and_(
                    ExamCategory.subject_id == subject_id,
                    ExamCategory.enabled == True,
                    ExamCategory.parent_id.is_(None)  # 顶级分类
                )
            )
            .order_by(ExamCategory.order_num)
        )
        result = await self.session.exec(stmt)
        categories = result.all()

        # 排除自身及其子孙
        exclude_ids = {exclude_id} if exclude_id else set()

        # 如果需要排除子孙，需要递归查询
        if exclude_id:
            descendants = await self._get_descendant_ids(exclude_id)
            exclude_ids.update(descendants)

        # 过滤排除的分类
        filtered = [c for c in categories if c.id not in exclude_ids]

        return [self._to_response(c) for c in filtered]

    async def _get_descendant_ids(self, category_id: int) -> set:
        """递归获取分类的所有子孙ID"""
        stmt = select(ExamCategory.id).where(ExamCategory.parent_id == category_id)
        result = await self.session.exec(stmt)
        child_ids = set(result.all())

        all_descendants = set(child_ids)
        for child_id in child_ids:
            descendants = await self._get_descendant_ids(child_id)
            all_descendants.update(descendants)

        return all_descendants

    async def check_category_usage(self, category_id: int) -> int:
        """
        检查分类被引用次数（真题+模拟题）

        Args:
            category_id: 分类ID

        Returns:
            被引用次数
        """
        # 获取分类信息
        result = await self.session.exec(
            select(ExamCategory).where(ExamCategory.id == category_id)
        )
        category = result.first()

        if category is None:
            raise NotFoundException(f"分类不存在：ID={category_id}")

        # 统计被真题引用次数
        question_count = await self._count_exam_questions(
            category.subject_id, category.name
        )
        # 统计被模拟题引用次数
        mock_count = await self._count_mock_questions(
            category.subject_id, category.name
        )

        return question_count + mock_count

    async def get_category_usage(self, category_id: int) -> ExamCategoryUsageResponse:
        """
        检查分类是否被引用

        Args:
            category_id: 分类ID

        Returns:
            引用检查结果
        """
        # 获取分类信息
        result = await self.session.exec(
            select(ExamCategory).where(ExamCategory.id == category_id)
        )
        category = result.first()

        if category is None:
            raise NotFoundException(f"分类不存在：ID={category_id}")

        # 检查是否有子分类
        children_count = await self.session.exec(
            select(func.count()).select_from(ExamCategory).where(
                ExamCategory.parent_id == category_id
            )
        )
        has_children = (children_count.one() or 0) > 0

        # 统计被引用次数
        question_count = await self._count_exam_questions(
            category.subject_id, category.name
        )
        mock_count = await self._count_mock_questions(
            category.subject_id, category.name
        )

        can_delete = not has_children and question_count == 0 and mock_count == 0

        return ExamCategoryUsageResponse(
            id=category.id,
            name=category.name,
            has_children=has_children,
            question_count=question_count,
            mock_count=mock_count,
            can_delete=can_delete
        )

    async def _count_exam_questions(
        self,
        subject_id: int,
        category_name: str
    ) -> int:
        """
        统计真题引用数量

        Args:
            subject_id: 科目ID
            category_name: 分类名称

        Returns:
            引用数量
        """
        # 使用JSON_CONTAINS进行JSON数组匹配
        # MySQL: JSON_CONTAINS(category, JSON_QUOTE(category_name))
        # SQLite: category LIKE '%' || category_name || '%' (简化版)
        stmt = (
            select(func.count())
            .select_from(ExamQuestion)
            .where(
                and_(
                    ExamQuestion.subject_id == subject_id,
                    ExamQuestion.category.isnot(None),
                    text("json_extract(category, '$') LIKE :pattern")
                )
            )
            .params(pattern=f'"{category_name}"%')
        )
        result = await self.session.exec(stmt)
        return result.one() or 0

    async def _count_mock_questions(
        self,
        subject_id: int,
        category_name: str
    ) -> int:
        """
        统计模拟题引用数量

        Args:
            subject_id: 科目ID
            category_name: 分类名称

        Returns:
            引用数量
        """
        stmt = (
            select(func.count())
            .select_from(MockQuestion)
            .where(
                and_(
                    MockQuestion.subject_id == subject_id,
                    MockQuestion.category.isnot(None),
                    text("json_extract(category, '$') LIKE :pattern")
                )
            )
            .params(pattern=f'"{category_name}"%')
        )
        result = await self.session.exec(stmt)
        return result.one() or 0

    async def get_by_id(self, category_id: int) -> ExamCategoryResponse:
        """
        按ID查询分类

        Args:
            category_id: 分类ID

        Returns:
            分类详情

        Raises:
            NotFoundException: 分类不存在
        """
        logger.info("ExamCategoryService.get_by_id started, category_id: %d", category_id)
        result = await self.session.exec(
            select(ExamCategory).where(ExamCategory.id == category_id)
        )
        category = result.first()

        if category is None:
            logger.warning("ExamCategoryService.get_by_id: category not found, id: %d", category_id)
            raise NotFoundException(f"分类不存在：ID={category_id}")

        response = self._to_response(category)
        logger.info("ExamCategoryService.get_by_id completed, category_id: %d", category_id)
        return response

    async def create(
        self,
        request: ExamCategoryCreateRequest
    ) -> ExamCategoryResponse:
        """
        创建分类

        Args:
            request: 创建请求

        Returns:
            创建的分类

        Raises:
            NotFoundException: 父分类不存在
            ConflictException: 名称或编码已存在
        """
        logger.info("ExamCategoryService.create started, subject_id: %d, name: %s",
                    request.subject_id, request.name)

        # 检查父分类是否存在（如果指定了parent_id）
        if request.parent_id is not None:
            parent_result = await self.session.exec(
                select(ExamCategory).where(ExamCategory.id == request.parent_id)
            )
            parent = parent_result.first()
            if parent is None:
                logger.warning("ExamCategoryService.create: parent category not found, parent_id: %d",
                               request.parent_id)
                raise NotFoundException(f"父分类不存在：ID={request.parent_id}")

            # 验证父分类属于同一科目
            if parent.subject_id != request.subject_id:
                logger.warning("ExamCategoryService.create: parent category belongs to different subject")
                raise ConflictException("父分类不属于指定的科目")

        # 检查名称唯一性
        name_count = await self.session.exec(
            select(func.count()).select_from(ExamCategory).where(
                and_(
                    ExamCategory.subject_id == request.subject_id,
                    ExamCategory.name == request.name
                )
            )
        )
        if name_count.one() > 0:
            logger.warning("ExamCategoryService.create failed: category name already exists: %s", request.name)
            raise ConflictException(f"分类名称已存在：{request.name}")

        # 检查编码唯一性
        code_count = await self.session.exec(
            select(func.count()).select_from(ExamCategory).where(
                and_(
                    ExamCategory.subject_id == request.subject_id,
                    ExamCategory.code == request.code
                )
            )
        )
        if code_count.one() > 0:
            logger.warning("ExamCategoryService.create failed: category code already exists: %s", request.code)
            raise ConflictException(f"分类编码已存在：{request.code}")

        # 创建分类
        category = ExamCategory(
            subject_id=request.subject_id,
            parent_id=request.parent_id,
            name=request.name,
            code=request.code,
            description=request.description,
            order_num=request.order_num,
            enabled=request.enabled
        )
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)

        logger.info("ExamCategoryService.create completed, category_id: %d", category.id)
        return self._to_response(category)

    async def update(
        self,
        category_id: int,
        request: ExamCategoryUpdateRequest
    ) -> ExamCategoryResponse:
        """
        更新分类

        Args:
            category_id: 分类ID
            request: 更新请求

        Returns:
            更新后的分类

        Raises:
            NotFoundException: 分类不存在
            ConflictException: 名称或编码已存在
        """
        logger.info("ExamCategoryService.update started, category_id: %d", category_id)

        # 检查分类是否存在
        result = await self.session.exec(
            select(ExamCategory).where(ExamCategory.id == category_id)
        )
        category = result.first()

        if category is None:
            logger.warning("ExamCategoryService.update: category not found, id: %d", category_id)
            raise NotFoundException(f"分类不存在：ID={category_id}")

        # 检查新的父分类是否存在（如果指定了新的parent_id）
        if request.parent_id is not None and request.parent_id != category.parent_id:
            if request.parent_id == category_id:
                logger.warning("ExamCategoryService.update: cannot set category as its own parent")
                raise ConflictException("不能将分类设置为自己的父分类")

            parent_result = await self.session.exec(
                select(ExamCategory).where(ExamCategory.id == request.parent_id)
            )
            parent = parent_result.first()
            if parent is None:
                logger.warning("ExamCategoryService.update: parent category not found, parent_id: %d",
                               request.parent_id)
                raise NotFoundException(f"父分类不存在：ID={request.parent_id}")

            subject_id = request.subject_id or category.subject_id
            if parent.subject_id != subject_id:
                logger.warning("ExamCategoryService.update: parent category belongs to different subject")
                raise ConflictException("父分类不属于指定的科目")

        # 检查名称唯一性（排除自身）
        subject_id = request.subject_id or category.subject_id
        if request.name is not None and request.name != category.name:
            name_count = await self.session.exec(
                select(func.count()).select_from(ExamCategory).where(
                    and_(
                        ExamCategory.subject_id == subject_id,
                        ExamCategory.name == request.name,
                        ExamCategory.id != category_id
                    )
                )
            )
            if name_count.one() > 0:
                logger.warning("ExamCategoryService.update failed: category name conflict: %s", request.name)
                raise ConflictException(f"分类名称已被其他分类使用：{request.name}")

        # 检查编码唯一性（排除自身）
        if request.code is not None and request.code != category.code:
            code_count = await self.session.exec(
                select(func.count()).select_from(ExamCategory).where(
                    and_(
                        ExamCategory.subject_id == subject_id,
                        ExamCategory.code == request.code,
                        ExamCategory.id != category_id
                    )
                )
            )
            if code_count.one() > 0:
                logger.warning("ExamCategoryService.update failed: category code conflict: %s", request.code)
                raise ConflictException(f"分类编码已被其他分类使用：{request.code}")

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        await self.session.commit()
        await self.session.refresh(category)

        logger.info("ExamCategoryService.update completed, category_id: %d", category_id)
        return self._to_response(category)

    async def delete(self, category_id: int) -> None:
        """
        删除分类

        Args:
            category_id: 分类ID

        Raises:
            NotFoundException: 分类不存在
            ConflictException: 分类被引用或存在子分类
        """
        logger.info("ExamCategoryService.delete started, category_id: %d", category_id)

        # 检查分类是否存在
        result = await self.session.exec(
            select(ExamCategory).where(ExamCategory.id == category_id)
        )
        category = result.first()

        if category is None:
            logger.warning("ExamCategoryService.delete: category not found, id: %d", category_id)
            raise NotFoundException(f"分类不存在：ID={category_id}")

        # 检查是否有子分类
        children_count = await self.session.exec(
            select(func.count()).select_from(ExamCategory).where(
                ExamCategory.parent_id == category_id
            )
        )
        if (children_count.one() or 0) > 0:
            logger.warning("ExamCategoryService.delete failed: category has children")
            raise ConflictException("该分类存在子分类，无法删除")

        # 检查是否被真题引用
        question_count = await self._count_exam_questions(
            category.subject_id, category.name
        )
        if question_count > 0:
            logger.warning("ExamCategoryService.delete failed: category referenced by %d exam questions",
                           question_count)
            raise ConflictException(f"该分类被 {question_count} 道真题引用，无法删除")

        # 检查是否被模拟题引用
        mock_count = await self._count_mock_questions(
            category.subject_id, category.name
        )
        if mock_count > 0:
            logger.warning("ExamCategoryService.delete failed: category referenced by %d mock questions",
                           mock_count)
            raise ConflictException(f"该分类被 {mock_count} 道模拟题引用，无法删除")

        # 删除分类
        await self.session.delete(category)
        await self.session.commit()

        logger.info("ExamCategoryService.delete completed, category_id: %d", category_id)

    def _to_response(self, category: ExamCategory) -> ExamCategoryResponse:
        """将实体转换为响应对象"""
        return ExamCategoryResponse(
            id=category.id,
            subject_id=category.subject_id,
            subject_name=None,  # 需要额外查询
            parent_id=category.parent_id,
            parent_name=None,  # 需要额外查询
            name=category.name,
            code=category.code,
            description=category.description,
            order_num=category.order_num,
            enabled=category.enabled,
            question_count=None,  # 单独统计
            create_time=category.create_time.isoformat() if category.create_time else None,
            update_time=category.update_time.isoformat() if category.update_time else None
        )
