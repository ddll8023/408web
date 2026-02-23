"""
章节管理服务模块
实现章节CRUD和树形结构业务逻辑
"""
from typing import List, Optional
from collections import defaultdict
from sqlmodel import select, func, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.entities import Chapter
from app.exception import NotFoundException, ConflictException
from app.schemas.chapter import (
    ChapterCreateRequest,
    ChapterUpdateRequest,
    ChapterResponse,
    ChapterTreeResponse
)
from app.utils.logger import setup_logger


# 获取服务日志记录器
logger = setup_logger(__name__)


class ChapterService:
    """章节服务类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_chapters_by_subject(
        self,
        subject_id: int,
        enabled_only: bool = False
    ) -> List[ChapterResponse]:
        """
        根据科目ID查询章节列表

        Args:
            subject_id: 科目ID
            enabled_only: 是否仅查询启用的章节

        Returns:
            章节列表（扁平）
        """
        logger.info("ChapterService.get_chapters_by_subject started, subject_id: %d, enabled_only: %s",
                    subject_id, enabled_only)
        conditions = [Chapter.subject_id == subject_id]
        if enabled_only:
            conditions.append(Chapter.enabled == True)

        stmt = select(Chapter).where(*conditions).order_by(Chapter.order_num)
        result = await self.session.exec(stmt)
        chapters = result.all()

        logger.info("ChapterService.get_chapters_by_subject completed, subject_id: %d, count: %d",
                    subject_id, len(chapters))
        return [self._to_response(c) for c in chapters]

    async def get_chapter_tree(
        self,
        subject_id: int,
        enabled_only: bool = False
    ) -> List[ChapterTreeResponse]:
        """
        查询章节树形结构

        遵循KISS原则：简单的两级树形结构
        使用内存分组算法构建树形，时间复杂度O(n)

        Args:
            subject_id: 科目ID
            enabled_only: 是否仅查询启用的章节

        Returns:
            章节树形结构列表
        """
        logger.info("ChapterService.get_chapter_tree started, subject_id: %d, enabled_only: %s",
                    subject_id, enabled_only)

        # 第一步：查询所有章节
        chapters = await self.get_chapters_by_subject(subject_id, enabled_only)

        if not chapters:
            logger.info("ChapterService.get_chapter_tree completed, subject_id: %d, tree is empty", subject_id)
            return []

        # 第二步：构建树形结构
        tree = self._build_tree(chapters)

        logger.info("ChapterService.get_chapter_tree completed, subject_id: %d, tree_nodes: %d",
                    subject_id, len(tree))
        return tree

    def _build_tree(
        self,
        chapters: List[ChapterResponse]
    ) -> List[ChapterTreeResponse]:
        """
        构建章节树形结构（内存分组算法）

        Args:
            chapters: 扁平章节列表

        Returns:
            树形结构列表
        """
        # 1. 转换为树形VO对象列表，初始化children为空列表
        chapter_map: dict[int, ChapterTreeResponse] = {}
        for c in chapters:
            chapter_map[c.id] = ChapterTreeResponse(
                id=c.id,
                subject_id=c.subject_id,
                parent_id=c.parent_id,
                name=c.name,
                order_num=c.order_num,
                enabled=c.enabled,
                children=[]
            )

        # 2. 按父ID分组，构建子节点映射
        children_map: dict[Optional[int], List[ChapterTreeResponse]] = defaultdict(list)
        for chapter in chapter_map.values():
            children_map[chapter.parent_id].append(chapter)

        # 3. 构建树形结构：顶级章节设置子章节列表
        tree: List[ChapterTreeResponse] = []
        for chapter in chapter_map.values():
            if chapter.parent_id is None:
                # 顶级章节：设置子章节
                chapter.children = children_map.get(chapter.id, [])
                tree.append(chapter)

        # 4. 按order_num排序
        tree.sort(key=lambda x: x.order_num)
        for chapter in tree:
            if chapter.children:
                chapter.children.sort(key=lambda x: x.order_num)

        return tree

    async def get_by_id(self, chapter_id: int) -> ChapterResponse:
        """
        按ID查询章节

        Args:
            chapter_id: 章节ID

        Returns:
            章节详情

        Raises:
            NotFoundException: 章节不存在
        """
        logger.info("ChapterService.get_by_id started, chapter_id: %d", chapter_id)
        result = await self.session.exec(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = result.first()

        if chapter is None:
            logger.warning("ChapterService.get_by_id: chapter not found, id: %d", chapter_id)
            raise NotFoundException(f"章节不存在：ID={chapter_id}")

        response = self._to_response(chapter)
        logger.info("ChapterService.get_by_id completed, chapter_id: %d", chapter_id)
        return response

    async def create(self, request: ChapterCreateRequest) -> ChapterResponse:
        """
        创建章节

        Args:
            request: 创建请求

        Returns:
            创建的章节

        Raises:
            NotFoundException: 父章节不存在
            ConflictException: 章节名称已存在
        """
        logger.info("ChapterService.create started, subject_id: %d, name: %s",
                    request.subject_id, request.name)

        # 检查父章节是否存在（如果指定了parent_id）
        if request.parent_id is not None:
            parent_result = await self.session.exec(
                select(Chapter).where(Chapter.id == request.parent_id)
            )
            parent = parent_result.first()
            if parent is None:
                logger.warning("ChapterService.create: parent chapter not found, parent_id: %d",
                               request.parent_id)
                raise NotFoundException(f"父章节不存在：ID={request.parent_id}")

            # 验证父章节属于同一科目
            if parent.subject_id != request.subject_id:
                logger.warning("ChapterService.create: parent chapter belongs to different subject")
                raise ConflictException("父章节不属于指定的科目")

        # 检查名称在同一父节点下是否唯一
        name_count = await self.session.exec(
            select(func.count()).select_from(Chapter).where(
                and_(
                    Chapter.subject_id == request.subject_id,
                    Chapter.parent_id == request.parent_id,
                    Chapter.name == request.name
                )
            )
        )
        if name_count.first() > 0:
            logger.warning("ChapterService.create failed: chapter name already exists: %s", request.name)
            raise ConflictException(f"章节名称已存在：{request.name}")

        # 创建章节
        chapter = Chapter(
            subject_id=request.subject_id,
            parent_id=request.parent_id,
            name=request.name,
            order_num=request.order_num,
            enabled=request.enabled
        )
        self.session.add(chapter)
        await self.session.refresh(chapter)

        logger.info("ChapterService.create completed, chapter_id: %d", chapter.id)
        return self._to_response(chapter)

    async def update(
        self,
        chapter_id: int,
        request: ChapterUpdateRequest
    ) -> ChapterResponse:
        """
        更新章节

        Args:
            chapter_id: 章节ID
            request: 更新请求

        Returns:
            更新后的章节

        Raises:
            NotFoundException: 章节不存在
            ConflictException: 名称已存在或无法将章节移至无效的父节点
        """
        logger.info("ChapterService.update started, chapter_id: %d", chapter_id)

        # 检查章节是否存在
        result = await self.session.exec(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = result.first()

        if chapter is None:
            logger.warning("ChapterService.update: chapter not found, id: %d", chapter_id)
            raise NotFoundException(f"章节不存在：ID={chapter_id}")

        # 检查新的父章节是否存在（如果指定了新的parent_id）
        if request.parent_id is not None and request.parent_id != chapter.parent_id:
            # 不能将章节设置为自己或自己的子章节为父节点（避免循环引用）
            if request.parent_id == chapter_id:
                logger.warning("ChapterService.update: cannot set chapter as its own parent")
                raise ConflictException("不能将章节设置为自己的父章节")

            parent_result = await self.session.exec(
                select(Chapter).where(Chapter.id == request.parent_id)
            )
            parent = parent_result.first()
            if parent is None:
                logger.warning("ChapterService.update: parent chapter not found, parent_id: %d",
                               request.parent_id)
                raise NotFoundException(f"父章节不存在：ID={request.parent_id}")

            # 验证父章节属于同一科目
            subject_id = request.subject_id or chapter.subject_id
            if parent.subject_id != subject_id:
                logger.warning("ChapterService.update: parent chapter belongs to different subject")
                raise ConflictException("父章节不属于指定的科目")

        # 检查名称唯一性（排除自身，同一父节点下）
        subject_id = request.subject_id or chapter.subject_id
        parent_id = request.parent_id if request.parent_id is not None else chapter.parent_id

        if request.name is not None and request.name != chapter.name:
            name_count = await self.session.exec(
                select(func.count()).select_from(Chapter).where(
                    and_(
                        Chapter.subject_id == subject_id,
                        Chapter.parent_id == parent_id,
                        Chapter.name == request.name,
                        Chapter.id != chapter_id
                    )
                )
            )
            if name_count.first() > 0:
                logger.warning("ChapterService.update failed: chapter name conflict: %s", request.name)
                raise ConflictException(f"章节名称已被同级其他章节使用：{request.name}")

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(chapter, field, value)

        await self.session.refresh(chapter)

        logger.info("ChapterService.update completed, chapter_id: %d", chapter_id)
        return self._to_response(chapter)

    async def delete(self, chapter_id: int) -> None:
        """
        删除章节

        Args:
            chapter_id: 章节ID

        Raises:
            NotFoundException: 章节不存在
        """
        logger.info("ChapterService.delete started, chapter_id: %d", chapter_id)

        # 检查章节是否存在
        result = await self.session.exec(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = result.first()

        if chapter is None:
            logger.warning("ChapterService.delete: chapter not found, id: %d", chapter_id)
            raise NotFoundException(f"章节不存在：ID={chapter_id}")

        # 删除章节（级联删除子章节，由数据库外键约束处理）
        await self.session.delete(chapter)

        logger.info("ChapterService.delete completed, chapter_id: %d", chapter_id)

    def _to_response(self, chapter: Chapter) -> ChapterResponse:
        """将实体转换为响应对象"""
        return ChapterResponse(
            id=chapter.id,
            subject_id=chapter.subject_id,
            parent_id=chapter.parent_id,
            name=chapter.name,
            order_num=chapter.order_num,
            enabled=chapter.enabled,
            create_time=chapter.create_time.isoformat() if chapter.create_time else None,
            update_time=chapter.update_time.isoformat() if chapter.update_time else None
        )
