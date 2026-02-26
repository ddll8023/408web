"""
真题管理服务模块
实现真题CRUD、查询、统计业务逻辑
"""
import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from sqlmodel import select, func, and_, or_, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.sql.sqltypes import Integer
from app.models.entities import ExamQuestion, Subject, User
from app.exception import NotFoundException, ConflictException
from app.schemas.exam import (
    ExamQueryParams,
    ExamCreateRequest,
    ExamUpdateRequest,
    ExamResponse,
    ExamYearStatResponse,
    ExamCategoryStatItem,
    ExamCategoryStatsResponse,
    ExamDuplicateCheckResponse,
    ExamIndexItem,
    ExamIndexResponse,
    PaginatedExamResponse,
    ExportResultResponse
)
from app.utils.logger import setup_logger


# 获取服务日志记录器
logger = setup_logger(__name__)


class ExamService:
    """真题服务类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_paginated(
        self,
        params: ExamQueryParams
    ) -> PaginatedExamResponse:
        """
        分页查询真题

        Args:
            params: 查询参数

        Returns:
            分页结果
        """
        logger.info("ExamService.get_paginated started, page: %d, page_size: %d, year: %s, subject_id: %s",
                    params.page, params.page_size, params.year, params.subject_id)

        # 构建查询条件
        conditions = []
        exec_params = {}

        if params.year is not None:
            conditions.append(ExamQuestion.year == params.year)

        if params.subject_id is not None:
            conditions.append(ExamQuestion.subject_id == params.subject_id)

        if params.no_category is True:
            conditions.append(
                or_(
                    ExamQuestion.category.is_(None),
                    ExamQuestion.category == ""
                )
            )
        elif params.category is not None and params.category.strip():
            # 分类包含查询 - 使用 SQLAlchemy like
            pattern = f'%"{params.category}"%'
            conditions.append(
                and_(
                    ExamQuestion.category.isnot(None),
                    ExamQuestion.category.like(pattern)
                )
            )

        if params.keyword and params.keyword.strip():
            keyword_pattern = f'%{params.keyword}%'
            conditions.append(
                or_(
                    ExamQuestion.title.ilike(keyword_pattern),
                    ExamQuestion.content.ilike(keyword_pattern)
                )
            )

        # 查询总数
        count_stmt = select(func.count(ExamQuestion.id)).select_from(ExamQuestion).where(*conditions)
        count_result = await self.session.exec(count_stmt)
        total = count_result.first() or 0

        # 查询数据
        offset = (params.page - 1) * params.page_size
        order_column = self._get_order_column(params.sort_field)
        if params.sort_order == "asc":
            order_column = order_column.asc()
        else:
            order_column = order_column.desc()

        stmt = select(ExamQuestion).where(*conditions).order_by(order_column).offset(offset).limit(params.page_size)
        result = await self.session.exec(stmt)
        questions = result.all()

        # 转换为响应对象
        data_list = [await self._to_response(q) for q in questions]

        logger.info("ExamService.get_paginated completed, total: %d", total)

        return PaginatedExamResponse(
            data=data_list,
            total=total,
            page=params.page,
            page_size=params.page_size
        )

    def _get_order_column(self, sort_field: str):
        """获取排序字段"""
        field_map = {
            "year": ExamQuestion.year,
            "update_time": ExamQuestion.update_time,
            "question_number": ExamQuestion.question_number
        }
        return field_map.get(sort_field, ExamQuestion.update_time)

    async def get_by_id(self, question_id: int) -> ExamResponse:
        """
        按ID查询真题

        Args:
            question_id: 真题ID

        Returns:
            真题详情

        Raises:
            NotFoundException: 真题不存在
        """
        logger.info("ExamService.get_by_id started, question_id: %d", question_id)
        stmt = select(ExamQuestion).where(ExamQuestion.id == question_id)
        result = await self.session.exec(stmt)
        question = result.first()

        if question is None:
            logger.warning("ExamService.get_by_id: question not found, id: %d", question_id)
            raise NotFoundException(f"真题不存在：ID={question_id}")

        response = await self._to_response(question)
        logger.info("ExamService.get_by_id completed, question_id: %d", question_id)
        return response

    async def check_duplicate(
        self,
        year: int,
        question_number: Optional[int],
        exclude_id: Optional[int] = None
    ) -> ExamDuplicateCheckResponse:
        """
        检查真题是否重复（year + question_number 组合唯一）

        Args:
            year: 年份
            question_number: 题号
            exclude_id: 排除的ID（更新时使用）

        Returns:
            查重结果
        """
        logger.info("ExamService.check_duplicate started, year: %d, question_number: %s, exclude_id: %s",
                    year, question_number, exclude_id)
        conditions = [
            ExamQuestion.year == year,
            ExamQuestion.question_number == question_number
        ]

        if exclude_id is not None:
            conditions.append(ExamQuestion.id != exclude_id)

        stmt = select(ExamQuestion).where(and_(*conditions))
        result = await self.session.exec(stmt)
        existing = result.first()

        if existing:
            logger.info("ExamService.check_duplicate: duplicate found")
            return ExamDuplicateCheckResponse(
                is_duplicate=True,
                existing_question=await self._to_response(existing)
            )

        logger.info("ExamService.check_duplicate: no duplicate found")
        return ExamDuplicateCheckResponse(is_duplicate=False)

    async def get_year_stats(
        self,
        category: Optional[str] = None
    ) -> List[ExamYearStatResponse]:
        """
        获取年份统计

        Args:
            category: 可选分类筛选

        Returns:
            年份统计列表
        """
        logger.info("ExamService.get_year_stats started, category: %s", category)
        conditions = []

        if category and category.strip():
            pattern = f'%"{category}"%'
            conditions.append(
                and_(
                    ExamQuestion.category.isnot(None),
                    ExamQuestion.category.like(pattern)
                )
            )

        # 按年份分组统计
        stmt = (
            select(
                ExamQuestion.year,
                func.count().label("count"),
                func.sum(
                    func.cast(
                        func.if_(ExamQuestion.question_type == "CHOICE", 1, 0),
                        Integer
                    )
                ).label("choice_count")
            )
            .where(*conditions)
            .group_by(ExamQuestion.year)
            .order_by(ExamQuestion.year.desc())
        )

        result = await self.session.exec(stmt)
        rows = result.all()

        stats = []
        for row in rows:
            choice_count = row.choice_count or 0
            stats.append(ExamYearStatResponse(
                year=row.year,
                count=row.count,
                choice_count=choice_count,
                subjective_count=row.count - choice_count
            ))

        logger.info("ExamService.get_year_stats completed, count: %d", len(stats))
        return stats

    async def get_category_stats(
        self,
        subject_id: Optional[int] = None
    ) -> ExamCategoryStatsResponse:
        """
        获取分类统计（从JSON数组展开）

        Args:
            subject_id: 可选科目ID筛选

        Returns:
            分类统计结果
        """
        logger.info("ExamService.get_category_stats started, subject_id: %s", subject_id)
        conditions = [
            ExamQuestion.category.isnot(None),
            ExamQuestion.category != ""  # 简单字符串非空检查
        ]

        if subject_id:
            conditions.append(ExamQuestion.subject_id == subject_id)

        # 由于SQLite不支持JSON_TABLE，使用内存聚合方式
        # 先查询所有符合条件的记录
        stmt = select(ExamQuestion).where(*conditions)
        result = await self.session.exec(stmt)
        questions = result.all()

        # 内存中展开JSON数组进行统计
        category_counts: dict[str, dict] = {}
        for q in questions:
            if q.category:
                try:
                    categories = json.loads(q.category)
                    if isinstance(categories, list):
                        for cat in categories:
                            if cat not in category_counts:
                                category_counts[cat] = {"count": 0, "choice": 0, "subjective": 0}
                            category_counts[cat]["count"] += 1
                            if q.question_type == "CHOICE":
                                category_counts[cat]["choice"] += 1
                            else:
                                category_counts[cat]["subjective"] += 1
                except json.JSONDecodeError:
                    continue

        # 转换为响应列表
        stats_items = [
            ExamCategoryStatItem(
                category=cat,
                count=data["count"],
                choice_count=data["choice"],
                subjective_count=data["subjective"]
            )
            for cat, data in sorted(category_counts.items())
        ]

        # 获取科目信息
        subject_name = None
        if subject_id:
            subj_result = await self.session.exec(
                select(Subject).where(Subject.id == subject_id)
            )
            subject = subj_result.first()
            if subject:
                subject_name = subject.name

        logger.info("ExamService.get_category_stats completed, categories: %d", len(stats_items))

        return ExamCategoryStatsResponse(
            subject_id=subject_id,
            subject_name=subject_name,
            stats=stats_items
        )

    async def get_index(
        self,
        subject_id: Optional[int] = None
    ) -> ExamIndexResponse:
        """
        获取真题索引数据

        Args:
            subject_id: 可选科目ID筛选

        Returns:
            索引数据
        """
        logger.info("ExamService.get_index started, subject_id: %s", subject_id)
        conditions = []
        if subject_id:
            conditions.append(ExamQuestion.subject_id == subject_id)

        stmt = (
            select(ExamQuestion.id, ExamQuestion.year, ExamQuestion.question_number)
            .where(*conditions)
            .order_by(ExamQuestion.year.desc(), ExamQuestion.question_number.asc())
        )
        result = await self.session.exec(stmt)
        rows = result.all()

        index_data = [
            ExamIndexItem(
                id=row.id,
                year=row.year,
                question_number=row.question_number
            )
            for row in rows
        ]

        # 获取科目信息
        subject_name = None
        if subject_id:
            subj_result = await self.session.exec(
                select(Subject).where(Subject.id == subject_id)
            )
            subject = subj_result.first()
            if subject:
                subject_name = subject.name

        logger.info("ExamService.get_index completed, count: %d", len(index_data))

        return ExamIndexResponse(
            subject_id=subject_id,
            subject_name=subject_name,
            index_data=index_data
        )

    async def create(
        self,
        request: ExamCreateRequest,
        author_id: int
    ) -> ExamResponse:
        """
        创建真题

        Args:
            request: 创建请求
            author_id: 作者ID

        Returns:
            创建的真题

        Raises:
            ConflictException: 题目已存在
        """
        logger.info("ExamService.create started, year: %d, question_number: %s, subject_id: %d",
                    request.year, request.question_number, request.subject_id)

        # 查重检查
        if request.question_number is not None:
            dup_result = await self.check_duplicate(request.year, request.question_number)
            if dup_result.is_duplicate:
                logger.warning("ExamService.create failed: duplicate question")
                raise ConflictException(
                    f"年份 {request.year} 的题号 {request.question_number} 已存在"
                )

        # 创建真题
        question = ExamQuestion(
            year=request.year,
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
        await self.session.refresh(question)

        logger.info("ExamService.create completed, question_id: %d", question.id)
        return await self._to_response(question)

    async def update(
        self,
        question_id: int,
        request: ExamUpdateRequest
    ) -> ExamResponse:
        """
        更新真题

        Args:
            question_id: 真题ID
            request: 更新请求

        Returns:
            更新后的真题

        Raises:
            NotFoundException: 真题不存在
            ConflictException: 题目已存在
        """
        logger.info("ExamService.update started, question_id: %d", question_id)

        # 查询真题
        stmt = select(ExamQuestion).where(ExamQuestion.id == question_id)
        result = await self.session.exec(stmt)
        question = result.first()

        if question is None:
            logger.warning("ExamService.update: question not found, id: %d", question_id)
            raise NotFoundException(f"真题不存在：ID={question_id}")

        # 检查唯一性冲突
        new_year = request.year if request.year is not None else question.year
        new_number = request.question_number if request.question_number is not None else question.question_number

        if new_number is not None:
            year_changed = new_year != question.year
            number_changed = new_number != question.question_number

            if year_changed or number_changed:
                dup_result = await self.check_duplicate(new_year, new_number, question_id)
                if dup_result.is_duplicate:
                    logger.warning("ExamService.update failed: duplicate question")
                    raise ConflictException(
                        f"年份 {new_year} 的题号 {new_number} 已存在"
                    )

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)

        await self.session.refresh(question)

        logger.info("ExamService.update completed, question_id: %d", question_id)
        return await self._to_response(question)

    async def delete(self, question_id: int) -> None:
        """
        删除真题

        Args:
            question_id: 真题ID

        Raises:
            NotFoundException: 真题不存在
        """
        logger.info("ExamService.delete started, question_id: %d", question_id)

        # 查询真题
        stmt = select(ExamQuestion).where(ExamQuestion.id == question_id)
        result = await self.session.exec(stmt)
        question = result.first()

        if question is None:
            logger.warning("ExamService.delete: question not found, id: %d", question_id)
            raise NotFoundException(f"真题不存在：ID={question_id}")

        # 删除
        await self.session.delete(question)

        logger.info("ExamService.delete completed, question_id: %d", question_id)

    async def _to_response(self, question: ExamQuestion) -> ExamResponse:
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

        # 解析 category JSON 字符串为数组
        category_list = None
        if question.category:
            try:
                category_list = json.loads(question.category)
                if not isinstance(category_list, list):
                    category_list = None
            except json.JSONDecodeError:
                category_list = None

        return ExamResponse(
            id=question.id,
            year=question.year,
            question_number=question.question_number,
            question_type=question.question_type,
            title=question.title,
            content=question.content,
            options=question.options,
            answer=question.answer,
            category=category_list,
            subject_id=question.subject_id,
            subject_name=subject_name,
            difficulty=question.difficulty,
            author_id=question.author_id,
            author_name=author_name,
            create_time=question.create_time.isoformat() if question.create_time else None,
            update_time=question.update_time.isoformat() if question.update_time else None
        )

    async def find_by_year(
        self,
        year: int,
        category: Optional[str] = None,
        subject_id: Optional[int] = None
    ) -> List[ExamResponse]:
        """
        根据年份查询真题列表

        Args:
            year: 年份
            category: 可选分类筛选
            subject_id: 可选科目ID筛选

        Returns:
            符合条件的真题列表
        """
        logger.info("ExamService.find_by_year started, year: %d, category: %s, subject_id: %s",
                    year, category, subject_id)
        conditions = [ExamQuestion.year == year]

        if subject_id:
            conditions.append(ExamQuestion.subject_id == subject_id)

        if category and category.strip():
            pattern = f'%"{category}"%'
            conditions.append(
                and_(
                    ExamQuestion.category.isnot(None),
                    ExamQuestion.category.like(pattern)
                )
            )

        stmt = (
            select(ExamQuestion)
            .where(*conditions)
            .order_by(ExamQuestion.question_number)
        )

        result = await self.session.exec(stmt)
        questions = result.all()
        responses = [await self._to_response(q) for q in questions]

        logger.info("ExamService.find_by_year completed, count: %d", len(responses))
        return responses

    async def get_categories_by_subject(self, subject_id: int) -> List[str]:
        """
        查询科目下实际存在真题的分类列表

        Args:
            subject_id: 科目ID

        Returns:
            分类名列表（去重）
        """
        logger.info("ExamService.get_categories_by_subject started, subject_id: %d", subject_id)
        stmt = (
            select(ExamQuestion.category)
            .where(
                and_(
                    ExamQuestion.subject_id == subject_id,
                    ExamQuestion.category.isnot(None)
                )
            )
        )
        result = await self.session.exec(stmt)
        categories = result.all()

        # 从JSON数组中提取并去重
        category_set = set()
        for cat_json in categories:
            if cat_json:
                try:
                    cats = json.loads(cat_json)
                    if isinstance(cats, list):
                        category_set.update(cats)
                except json.JSONDecodeError:
                    continue

        categories_list = sorted(list(category_set))
        logger.info("ExamService.get_categories_by_subject completed, count: %d", len(categories_list))
        return categories_list

    async def find_all_for_index(
        self,
        category: Optional[str] = None
    ) -> List[ExamResponse]:
        """
        查询用于年份导航的真题索引数据

        Args:
            category: 可选分类筛选

        Returns:
            简化的真题列表（用于索引）
        """
        logger.info("ExamService.find_all_for_index started, category: %s", category)
        conditions = []
        if category and category.strip():
            pattern = f'%"{category}"%'
            conditions.append(
                and_(
                    ExamQuestion.category.isnot(None),
                    ExamQuestion.category.like(pattern)
                )
            )

        stmt = (
            select(ExamQuestion)
            .where(*conditions)
            .order_by(ExamQuestion.year.desc(), ExamQuestion.question_number.asc())
        )

        result = await self.session.exec(stmt)
        questions = result.all()
        responses = [await self._to_response(q) for q in questions]

        logger.info("ExamService.find_all_for_index completed, count: %d", len(responses))
        return responses

    async def find_for_nav_index(
        self,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        查询用于侧边栏导航的轻量级真题索引数据

        Args:
            category: 可选分类筛选

        Returns:
            轻量级真题列表（仅包含导航所需字段）
        """
        logger.info("ExamService.find_for_nav_index started, category: %s", category)
        conditions = []
        if category and category.strip():
            pattern = f'%"{category}"%'
            conditions.append(
                and_(
                    ExamQuestion.category.isnot(None),
                    ExamQuestion.category.like(pattern)
                )
            )

        # 只查询导航所需的5个字段
        stmt = (
            select(
                ExamQuestion.id,
                ExamQuestion.year,
                ExamQuestion.question_number,
                ExamQuestion.title,
                ExamQuestion.category
            )
            .where(*conditions)
            .order_by(ExamQuestion.year.desc(), ExamQuestion.question_number.asc())
        )

        result = await self.session.exec(stmt)
        rows = result.all()

        # 转换为字典列表
        nav_items = []
        for row in rows:
            # 解析 category 字段（JSON字符串 -> 列表）
            category_str = row.category
            category_list = json.loads(category_str) if category_str else None

            nav_items.append({
                "id": row.id,
                "year": row.year,
                "questionNumber": row.question_number,
                "title": row.title,
                "category": category_list
            })

        logger.info("ExamService.find_for_nav_index completed, count: %d", len(nav_items))
        return nav_items

    async def find_by_subject_and_category(
        self,
        subject_id: Optional[int],
        category: str
    ) -> List[ExamResponse]:
        """
        根据科目和分类查询真题

        Args:
            subject_id: 可选科目ID
            category: 分类名称

        Returns:
            符合条件的真题列表
        """
        logger.info("ExamService.find_by_subject_and_category started, subject_id: %s, category: %s",
                    subject_id, category)
        conditions = []
        pattern = f'%"{category}"%'
        conditions.append(
            and_(
                ExamQuestion.category.isnot(None),
                ExamQuestion.category.like(pattern)
            )
        )

        if subject_id:
            conditions.append(ExamQuestion.subject_id == subject_id)

        stmt = (
            select(ExamQuestion)
            .where(*conditions)
            .order_by(ExamQuestion.year.desc(), ExamQuestion.question_number.asc())
        )

        result = await self.session.exec(stmt)
        questions = result.all()
        responses = [await self._to_response(q) for q in questions]

        logger.info("ExamService.find_by_subject_and_category completed, count: %d", len(responses))
        return responses

    async def export_by_subject(
        self,
        subject_id: int,
        format: str = "markdown"
    ) -> ExportResultResponse:
        """
        按科目导出真题

        Args:
            subject_id: 科目ID
            format: 导出格式（markdown）

        Returns:
            导出结果
        """
        logger.info("ExamService.export_by_subject started, subject_id: %d, format: %s", subject_id, format)

        # 查询该科目的所有真题
        stmt = (
            select(ExamQuestion)
            .where(ExamQuestion.subject_id == subject_id)
            .order_by(ExamQuestion.year.desc(), ExamQuestion.question_number.asc())
        )
        result = await self.session.exec(stmt)
        questions = result.all()

        # 生成Markdown内容
        md_content = self._generate_markdown(questions)

        # 编码文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"真题_{subject_id}_{timestamp}.md"

        logger.info("ExamService.export_by_subject completed, count: %d", len(questions))

        return ExportResultResponse(
            filename=filename,
            content_type="text/markdown; charset=utf-8",
            file_bytes=md_content.encode("utf-8")
        )

    def _generate_markdown(self, questions: List[ExamQuestion]) -> str:
        """生成Markdown格式的真题内容"""
        md_lines = ["# 真题列表\n"]

        # 按年份分组
        year_groups = {}
        for q in questions:
            year = q.year
            if year not in year_groups:
                year_groups[year] = []
            year_groups[year].append(q)

        for year in sorted(year_groups.keys(), reverse=True):
            md_lines.append(f"## {year}年\n")
            for q in year_groups[year]:
                md_lines.append(f"### 第{q.question_number}题")
                if q.title:
                    md_lines.append(f"**{q.title}**")
                md_lines.append("")
                md_lines.append(q.content)
                if q.options:
                    md_lines.append("**选项：**")
                    try:
                        opts = json.loads(q.options)
                        for k, v in opts.items():
                            md_lines.append(f"- **{k}**: {v}")
                    except:
                        md_lines.append(q.options)
                md_lines.append("")
                if q.answer:
                    md_lines.append(f"**答案：** {q.answer}")
                md_lines.append("---")
                md_lines.append("")

        return "\n".join(md_lines)
