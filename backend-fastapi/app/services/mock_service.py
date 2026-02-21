"""
模拟题管理服务模块
实现模拟题CRUD、查询、统计业务逻辑
"""
from typing import List, Optional
from sqlmodel import select, func, and_, or_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.entities import MockQuestion, Subject, User
from app.exception import NotFoundException, ConflictException
from app.schemas.mock import (
    MockQueryParams,
    MockCreateRequest,
    MockUpdateRequest,
    MockResponse,
    MockSourceStatResponse,
    MockSourceItem,
    MockSourcesResponse,
    MockCategoryStatItem,
    MockCategoryStatsResponse,
    MockDuplicateCheckResponse,
    PaginatedMockResponse
)
from app.utils.logger import setup_logger


# 获取服务日志记录器
logger = setup_logger(__name__)


class MockService:
    """模拟题服务类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_paginated(
        self,
        params: MockQueryParams
    ) -> PaginatedMockResponse:
        """
        分页查询模拟题

        Args:
            params: 查询参数

        Returns:
            分页结果
        """
        logger.info("MockService.get_paginated started, page: %d, page_size: %d, source: %s, subject_id: %s",
                    params.page, params.page_size, params.source, params.subject_id)

        # 构建查询条件
        conditions = self._build_query_conditions(params)

        # 查询总数
        count_stmt = select(func.count()).select_from(MockQuestion).where(*conditions)
        count_result = await self.session.exec(count_stmt)
        total = count_result.first() or 0

        # 查询数据
        offset = (params.page - 1) * params.page_size
        order_column = self._get_order_column(params.sort_field)
        if params.sort_order == "asc":
            order_column = order_column.asc()
        else:
            order_column = order_column.desc()

        stmt = select(MockQuestion).where(*conditions).order_by(order_column).offset(offset).limit(params.page_size)
        result = await self.session.exec(stmt)
        questions = result.all()

        # 转换为响应对象
        data_list = [await self._to_response(q) for q in questions]

        logger.info("MockService.get_paginated completed, total: %d", total)

        return PaginatedMockResponse(
            data_list=data_list,
            total=total,
            page=params.page,
            page_size=params.page_size
        )

    def _build_query_conditions(self, params: MockQueryParams) -> List:
        """构建查询条件列表"""
        conditions = []

        if params.source is not None:
            conditions.append(MockQuestion.source == params.source)

        if params.subject_id is not None:
            conditions.append(MockQuestion.subject_id == params.subject_id)

        if params.no_category is True:
            conditions.append(
                or_(
                    MockQuestion.category.is_(None),
                    text("json_extract(category, '$') IS NULL"),
                    text("json_length(category) = 0")
                )
            )
        elif params.category is not None:
            # 分类包含查询
            pattern = f'%"{params.category}"%'
            conditions.append(
                and_(
                    MockQuestion.category.isnot(None),
                    text("json_extract(category, '$') LIKE :cat_pattern")
                )
            )

        if params.keyword:
            keyword_pattern = f'%{params.keyword}%'
            conditions.append(
                or_(
                    MockQuestion.title.ilike(keyword_pattern),
                    MockQuestion.content.ilike(keyword_pattern)
                )
            )

        return conditions

    def _get_order_column(self, sort_field: str):
        """获取排序字段"""
        field_map = {
            "source": MockQuestion.source,
            "update_time": MockQuestion.update_time,
            "question_number": MockQuestion.question_number,
            "create_time": MockQuestion.create_time
        }
        return field_map.get(sort_field, MockQuestion.update_time)

    async def get_by_id(self, question_id: int) -> MockResponse:
        """
        按ID查询模拟题

        Args:
            question_id: 模拟题ID

        Returns:
            模拟题详情

        Raises:
            NotFoundException: 模拟题不存在
        """
        logger.info("MockService.get_by_id started, question_id: %d", question_id)
        stmt = select(MockQuestion).where(MockQuestion.id == question_id)
        result = await self.session.exec(stmt)
        question = result.first()

        if question is None:
            logger.warning("MockService.get_by_id: question not found, id: %d", question_id)
            raise NotFoundException(f"模拟题不存在：ID={question_id}")

        response = await self._to_response(question)
        logger.info("MockService.get_by_id completed, question_id: %d", question_id)
        return response

    async def check_duplicate(
        self,
        source: str,
        title: Optional[str],
        question_number: Optional[int],
        exclude_id: Optional[int] = None
    ) -> MockDuplicateCheckResponse:
        """
        检查模拟题是否重复（source + title + question_number 组合唯一）

        Args:
            source: 来源机构
            title: 标题
            question_number: 题号
            exclude_id: 排除的ID（更新时使用）

        Returns:
            查重结果
        """
        logger.info("MockService.check_duplicate started, source: %s, title: %s, question_number: %s, exclude_id: %s",
                    source, title, question_number, exclude_id)
        conditions = [
            MockQuestion.source == source,
            MockQuestion.title == title,
            MockQuestion.question_number == question_number
        ]

        if exclude_id is not None:
            conditions.append(MockQuestion.id != exclude_id)

        stmt = select(MockQuestion).where(and_(*conditions))
        result = await self.session.exec(stmt)
        existing = result.first()

        if existing:
            logger.info("MockService.check_duplicate: duplicate found")
            return MockDuplicateCheckResponse(
                is_duplicate=True,
                existing_question=await self._to_response(existing)
            )

        logger.info("MockService.check_duplicate: no duplicate found")
        return MockDuplicateCheckResponse(is_duplicate=False)

    async def get_source_stats(
        self,
        category: Optional[str] = None
    ) -> List[MockSourceStatResponse]:
        """
        获取来源统计

        Args:
            category: 可选分类筛选

        Returns:
            来源统计列表
        """
        conditions = [MockQuestion.source.isnot(None)]

        if category:
            pattern = f'%"{category}"%'
            conditions.append(
                and_(
                    MockQuestion.category.isnot(None),
                    text("json_extract(category, '$') LIKE :cat_pattern")
                )
            )

        stmt = (
            select(
                MockQuestion.source,
                func.count().label("count")
            )
            .where(*conditions)
            .group_by(MockQuestion.source)
            .order_by(func.count().desc())
        )

        if category:
            stmt = stmt.bindparams(cat_pattern=pattern)
        result = await self.session.exec(stmt)

        rows = result.all()

        return [
            MockSourceStatResponse(source=row.source, count=row.count)
            for row in rows
        ]

    async def get_sources(self) -> MockSourcesResponse:
        """
        获取所有来源列表及数量

        Returns:
            来源列表
        """
        stmt = (
            select(
                MockQuestion.source,
                func.count().label("question_count")
            )
            .group_by(MockQuestion.source)
            .order_by(MockQuestion.source)
        )
        result = await self.session.exec(stmt)
        rows = result.all()

        sources = [
            MockSourceItem(source=row.source, question_count=row.question_count)
            for row in rows
        ]

        return MockSourcesResponse(sources=sources)

    async def get_category_stats(
        self,
        subject_id: int
    ) -> MockCategoryStatsResponse:
        """
        获取模拟题分类统计

        Args:
            subject_id: 科目ID

        Returns:
            分类统计结果
        """
        conditions = [
            MockQuestion.subject_id == subject_id,
            MockQuestion.category.isnot(None),
            text("json_length(category) > 0")
        ]

        # 先查询所有符合条件的记录
        stmt = select(MockQuestion).where(*conditions)
        result = await self.session.exec(stmt)
        questions = result.all()

        # 内存中展开JSON数组进行统计
        category_counts: dict[str, int] = {}
        for q in questions:
            if q.category:
                import json
                try:
                    categories = json.loads(q.category)
                    if isinstance(categories, list):
                        for cat in categories:
                            category_counts[cat] = category_counts.get(cat, 0) + 1
                except json.JSONDecodeError:
                    continue

        # 转换为响应列表
        stats_items = [
            MockCategoryStatItem(category=cat, count=count)
            for cat, count in sorted(category_counts.items())
        ]

        # 获取科目信息
        subject_name = None
        subj_result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        subject = subj_result.first()
        if subject:
            subject_name = subject.name

        return MockCategoryStatsResponse(
            subject_id=subject_id,
            subject_name=subject_name,
            stats=stats_items
        )

    async def create(
        self,
        request: MockCreateRequest,
        author_id: int
    ) -> MockResponse:
        """
        创建模拟题

        Args:
            request: 创建请求
            author_id: 作者ID

        Returns:
            创建的模拟题

        Raises:
            ConflictException: 模拟题已存在
        """
        logger.info("MockService.create started, source: %s, title: %s, subject_id: %d",
                    request.source, request.title, request.subject_id)

        # 查重检查
        dup_result = await self.check_duplicate(
            request.source,
            request.title,
            request.question_number
        )
        if dup_result.is_duplicate:
            logger.warning("MockService.create failed: duplicate question")
            raise ConflictException("相同来源、标题和题号的模拟题已存在")

        # 创建模拟题
        question = MockQuestion(
            source=request.source,
            question_number=request.question_number,
            question_type=request.question_type,
            title=request.title,
            content=request.content,
            options=request.options,
            answer=request.answer,
            category=request.category,
            subject_id=request.subject_id,
            difficulty=request.difficulty,
            author_id=author_id
        )
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)

        logger.info("MockService.create completed, question_id: %d", question.id)
        return await self._to_response(question)

    async def update(
        self,
        question_id: int,
        request: MockUpdateRequest
    ) -> MockResponse:
        """
        更新模拟题

        Args:
            question_id: 模拟题ID
            request: 更新请求

        Returns:
            更新后的模拟题

        Raises:
            NotFoundException: 模拟题不存在
            ConflictException: 模拟题已存在
        """
        logger.info("MockService.update started, question_id: %d", question_id)

        # 查询模拟题
        stmt = select(MockQuestion).where(MockQuestion.id == question_id)
        result = await self.session.exec(stmt)
        question = result.first()

        if question is None:
            logger.warning("MockService.update: question not found, id: %d", question_id)
            raise NotFoundException(f"模拟题不存在：ID={question_id}")

        # 检查唯一性冲突
        new_source = request.source if request.source is not None else question.source
        new_title = request.title if request.title is not None else question.title
        new_number = request.question_number if request.question_number is not None else question.question_number

        source_changed = new_source != question.source
        title_changed = new_title != question.title
        number_changed = new_number != question.question_number

        if source_changed or title_changed or number_changed:
            dup_result = await self.check_duplicate(
                new_source, new_title, new_number, question_id
            )
            if dup_result.is_duplicate:
                logger.warning("MockService.update failed: duplicate question")
                raise ConflictException("相同来源、标题和题号的模拟题已存在")

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)

        await self.session.commit()
        await self.session.refresh(question)

        logger.info("MockService.update completed, question_id: %d", question_id)
        return await self._to_response(question)

    async def delete(self, question_id: int) -> None:
        """
        删除模拟题

        Args:
            question_id: 模拟题ID

        Raises:
            NotFoundException: 模拟题不存在
        """
        logger.info("MockService.delete started, question_id: %d", question_id)

        # 查询模拟题
        stmt = select(MockQuestion).where(MockQuestion.id == question_id)
        result = await self.session.exec(stmt)
        question = result.first()

        if question is None:
            logger.warning("MockService.delete: question not found, id: %d", question_id)
            raise NotFoundException(f"模拟题不存在：ID={question_id}")

        # 删除
        await self.session.delete(question)
        await self.session.commit()

        logger.info("MockService.delete completed, question_id: %d", question_id)

    async def _to_response(self, question: MockQuestion) -> MockResponse:
        """将实体转换为响应对象"""
        # 获取关联数据
        subject_name = None
        if question.subject_id:
            subj_result = await self.session.exec(
                select(Subject).where(Subject.id == question.subject_id)
            )
            subject = subj_result.first()
            if subject:
                subject_name = subject.name

        author_name = None
        if question.author_id:
            user_result = await self.session.exec(
                select(User).where(User.id == question.author_id)
            )
            user = user_result.first()
            if user:
                author_name = user.username

        return MockResponse(
            id=question.id,
            source=question.source,
            question_number=question.question_number,
            question_type=question.question_type,
            title=question.title,
            content=question.content,
            options=question.options,
            answer=question.answer,
            category=question.category,
            subject_id=question.subject_id,
            subject_name=subject_name,
            difficulty=question.difficulty,
            author_id=question.author_id,
            author_name=author_name,
            create_time=question.create_time.isoformat() if question.create_time else None,
            update_time=question.update_time.isoformat() if question.update_time else None
        )

    async def find_by_source(
        self,
        source: str,
        category: Optional[str] = None,
        subject_id: Optional[int] = None
    ) -> List[MockResponse]:
        """
        根据来源查询模拟题列表

        Args:
            source: 来源机构
            category: 可选分类筛选
            subject_id: 可选科目ID筛选

        Returns:
            符合条件的模拟题列表
        """
        conditions = [MockQuestion.source == source]

        if subject_id:
            conditions.append(MockQuestion.subject_id == subject_id)

        if category:
            pattern = f'%"{category}"%'
            conditions.append(
                and_(
                    MockQuestion.category.isnot(None),
                    text("json_extract(category, '$') LIKE :cat_pattern")
                )
            )

        stmt = (
            select(MockQuestion)
            .where(*conditions)
            .order_by(MockQuestion.question_number)
        )

        if category:
            stmt = stmt.bindparams(cat_pattern=pattern)
        result = await self.session.exec(stmt)

        questions = result.all()
        return [await self._to_response(q) for q in questions]

    async def find_categories_by_subject(self, subject_id: int) -> List[str]:
        """
        查询科目下实际存在模拟题的分类列表

        Args:
            subject_id: 科目ID

        Returns:
            分类名列表（去重）
        """
        stmt = (
            select(MockQuestion.category)
            .where(
                and_(
                    MockQuestion.subject_id == subject_id,
                    MockQuestion.category.isnot(None)
                )
            )
        )
        result = await self.session.exec(stmt)
        categories = result.all()

        # 从JSON数组中提取并去重
        category_set = set()
        import json
        for cat_json in categories:
            if cat_json:
                try:
                    cats = json.loads(cat_json)
                    if isinstance(cats, list):
                        category_set.update(cats)
                except json.JSONDecodeError:
                    continue

        return sorted(list(category_set))

    async def count_by_subject(self) -> List[dict]:
        """
        按科目统计模拟题数量

        Returns:
            各科目的模拟题数量统计列表
        """
        stmt = (
            select(
                Subject.id,
                Subject.name,
                func.count(MockQuestion.id).label("count")
            )
            .outerjoin(MockQuestion, MockQuestion.subject_id == Subject.id)
            .group_by(Subject.id, Subject.name)
            .order_by(Subject.name)
        )
        result = await self.session.exec(stmt)
        rows = result.all()

        return [
            {
                "subject_id": row.id,
                "subject_name": row.name,
                "count": row.count or 0
            }
            for row in rows
        ]

    async def get_titles_by_source(self, source: str) -> List[str]:
        """
        获取指定来源下所有不重复的标题列表

        Args:
            source: 来源机构

        Returns:
            标题列表（去重、排序）
        """
        stmt = (
            select(MockQuestion.title)
            .where(
                and_(
                    MockQuestion.source == source,
                    MockQuestion.title.isnot(None)
                )
            )
            .distinct()
            .order_by(MockQuestion.title)
        )
        result = await self.session.exec(stmt)
        titles = result.all()

        return [t[0] for t in titles if t[0]]
