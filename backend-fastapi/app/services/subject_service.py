"""
科目管理服务模块
实现科目CRUD业务逻辑
"""
from typing import List, Optional
from sqlmodel import select, func, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.entities import Subject, ExamQuestion
from app.exception import NotFoundException, ConflictException
from app.schemas.subject import (
    SubjectCreateRequest,
    SubjectUpdateRequest,
    SubjectResponse
)
from app.utils.logger import setup_logger


# 获取服务日志记录器
logger = setup_logger(__name__)


class SubjectService:
    """科目服务类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_subjects(self) -> List[SubjectResponse]:
        """
        查询所有科目

        Returns:
            科目列表（含禁用）
        """
        logger.info("SubjectService.get_all_subjects started")
        result = await self.session.exec(select(Subject).order_by(Subject.order_num))
        subjects = result.all()
        logger.info("SubjectService.get_all_subjects completed, count: %d", len(subjects))
        return [self._to_response(s) for s in subjects]

    async def get_enabled_subjects(self) -> List[SubjectResponse]:
        """
        查询启用的科目

        Returns:
            启用科目列表（带题目统计）
        """
        logger.info("SubjectService.get_enabled_subjects started")
        # 使用JOIN聚合查询获取题目统计
        stmt = (
            select(
                Subject.id,
                Subject.name,
                Subject.code,
                Subject.description,
                Subject.order_num,
                Subject.enabled,
                func.count(ExamQuestion.id).label("question_count")
            )
            .outerjoin(ExamQuestion, Subject.id == ExamQuestion.subject_id)
            .where(Subject.enabled == True)
            .group_by(Subject.id)
            .order_by(Subject.order_num)
        )
        result = await self.session.exec(stmt)
        rows = result.all()

        responses = []
        for row in rows:
            responses.append(SubjectResponse(
                id=row.id,
                name=row.name,
                code=row.code,
                description=row.description,
                order_num=row.order_num,
                enabled=row.enabled,
                question_count=row.question_count
            ))
        logger.info("SubjectService.get_enabled_subjects completed, count: %d", len(responses))
        return responses

    async def get_by_id(self, subject_id: int) -> SubjectResponse:
        """
        按ID查询科目

        Args:
            subject_id: 科目ID

        Returns:
            科目详情

        Raises:
            NotFoundException: 科目不存在
        """
        logger.info("SubjectService.get_by_id started, subject_id: %d", subject_id)
        result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        subject = result.first()

        if subject is None:
            logger.warning("SubjectService.get_by_id: subject not found, id: %d", subject_id)
            raise NotFoundException(f"科目不存在：ID={subject_id}")

        response = self._to_response(subject)
        logger.info("SubjectService.get_by_id completed, subject_id: %d", subject_id)
        return response

    async def get_by_code(self, code: str) -> SubjectResponse:
        """
        按编码查询科目

        Args:
            code: 科目编码

        Returns:
            科目详情

        Raises:
            NotFoundException: 科目不存在
        """
        logger.info("SubjectService.get_by_code started, code: %s", code)
        result = await self.session.exec(
            select(Subject).where(Subject.code == code)
        )
        subject = result.first()

        if subject is None:
            logger.warning("SubjectService.get_by_code: subject not found, code: %s", code)
            raise NotFoundException(f"科目不存在：编码={code}")

        response = self._to_response(subject)
        logger.info("SubjectService.get_by_code completed, code: %s", code)
        return response

    async def create(self, request: SubjectCreateRequest) -> SubjectResponse:
        """
        创建科目

        Args:
            request: 创建请求

        Returns:
            创建的科目

        Raises:
            ConflictException: 名称或编码已存在
        """
        logger.info("SubjectService.create started, name: %s, code: %s", request.name, request.code)

        # 检查名称唯一性
        name_count = await self.session.exec(
            select(func.count()).select_from(Subject).where(Subject.name == request.name)
        )
        if name_count.first() > 0:
            logger.warning("SubjectService.create failed: name already exists: %s", request.name)
            raise ConflictException(f"科目名称已存在：{request.name}")

        # 检查编码唯一性
        code_count = await self.session.exec(
            select(func.count()).select_from(Subject).where(Subject.code == request.code)
        )
        if code_count.first() > 0:
            logger.warning("SubjectService.create failed: code already exists: %s", request.code)
            raise ConflictException(f"科目编码已存在：{request.code}")

        # 创建科目
        subject = Subject(
            name=request.name,
            code=request.code,
            description=request.description,
            order_num=request.order_num,
            enabled=request.enabled
        )
        self.session.add(subject)
        await self.session.refresh(subject)

        logger.info("SubjectService.create completed, subject_id: %d", subject.id)
        return self._to_response(subject)

    async def update(
        self,
        subject_id: int,
        request: SubjectUpdateRequest
    ) -> SubjectResponse:
        """
        更新科目

        Args:
            subject_id: 科目ID
            request: 更新请求

        Returns:
            更新后的科目

        Raises:
            NotFoundException: 科目不存在
            ConflictException: 名称或编码已被使用
        """
        logger.info("SubjectService.update started, subject_id: %d", subject_id)

        # 检查科目是否存在
        result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        subject = result.first()

        if subject is None:
            logger.warning("SubjectService.update: subject not found, id: %d", subject_id)
            raise NotFoundException(f"科目不存在：ID={subject_id}")

        # 检查名称唯一性（排除自身）
        if request.name is not None and request.name != subject.name:
            name_count = await self.session.exec(
                select(func.count()).select_from(Subject).where(
                    and_(
                        Subject.name == request.name,
                        Subject.id != subject_id
                    )
                )
            )
            if name_count.first() > 0:
                logger.warning("SubjectService.update failed: name conflict: %s", request.name)
                raise ConflictException(f"科目名称已被其他科目使用：{request.name}")

        # 检查编码唯一性（排除自身）
        if request.code is not None and request.code != subject.code:
            code_count = await self.session.exec(
                select(func.count()).select_from(Subject).where(
                    and_(
                        Subject.code == request.code,
                        Subject.id != subject_id
                    )
                )
            )
            if code_count.first() > 0:
                logger.warning("SubjectService.update failed: code conflict: %s", request.code)
                raise ConflictException(f"科目编码已被其他科目使用：{request.code}")

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subject, field, value)

        await self.session.refresh(subject)

        logger.info("SubjectService.update completed, subject_id: %d", subject_id)
        return self._to_response(subject)

    async def delete(self, subject_id: int) -> None:
        """
        删除科目

        Args:
            subject_id: 科目ID

        Raises:
            NotFoundException: 科目不存在
        """
        logger.info("SubjectService.delete started, subject_id: %d", subject_id)

        # 检查科目是否存在
        result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        subject = result.first()

        if subject is None:
            logger.warning("SubjectService.delete: subject not found, id: %d", subject_id)
            raise NotFoundException(f"科目不存在：ID={subject_id}")

        # 删除科目（级联删除关联章节）
        await self.session.delete(subject)

        logger.info("SubjectService.delete completed, subject_id: %d", subject_id)

    def _to_response(self, subject: Subject) -> SubjectResponse:
        """将实体转换为响应对象"""
        return SubjectResponse(
            id=subject.id,
            name=subject.name,
            code=subject.code,
            description=subject.description,
            order_num=subject.order_num,
            enabled=subject.enabled,
            question_count=None  # 单独查询时无统计
        )
