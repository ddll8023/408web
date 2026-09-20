"""改编题写入用例。

该模块拥有改编题与来源引用的写入事务边界，查询与响应转换委托给查询 Service。
"""
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.exceptions import ConflictException, NotFoundException, ValidationException
from web408.modules.adaptation.models import AdaptationQuestion, AdaptationSource
from web408.modules.adaptation.query_service import AdaptationQueryService
from web408.modules.adaptation.repository import AdaptationRepository
from web408.modules.adaptation.schemas import (
    AdaptationCreateRequest,
    AdaptationResponse,
    AdaptationSourceRefInput,
    AdaptationUpdateRequest,
)
from web408.modules.catalog.read_service import CatalogReadService
from web408.modules.exam.read_service import ExamReadService
from web408.modules.question_content.serialization import (
    parse_categories,
    parse_options,
    serialize_categories,
    serialize_options,
)
from web408.modules.question_content.validation import validate_question_values


class AdaptationCommandService:
    """编排改编题新增、更新和删除。"""

    def __init__(self, session: AsyncSession, query_service: AdaptationQueryService) -> None:
        self.session = session
        self.repository = AdaptationRepository(session)
        self.query_service = query_service
        self.catalog_read_service = CatalogReadService(session)
        self.exam_read_service = ExamReadService(session)

    async def create(
        self,
        request: AdaptationCreateRequest,
        author_id: int,
    ) -> AdaptationResponse:
        """创建改编题与来源引用并提交事务。"""
        validate_question_values(request.question_type, request.content, request.options)
        await self.catalog_read_service.validate_question_scope(
            request.subject_id,
            request.category,
        )
        if request.title is not None and request.question_number is not None:
            duplicate = await self.query_service.check_duplicate(
                request.title,
                request.question_number,
                [],
            )
            if duplicate.is_duplicate:
                raise ConflictException(
                    f"改编题已存在：{request.title} 第 {request.question_number} 题"
                )

        question = AdaptationQuestion(
            title=request.title,
            question_number=request.question_number,
            question_type=request.question_type.value,
            content=request.content,
            options=serialize_options(request.options),
            answer=request.answer,
            category=serialize_categories(request.category),
            subject_id=request.subject_id,
            difficulty=request.difficulty.value if request.difficulty else None,
            author_id=author_id,
        )
        self.session.add(question)
        await self.session.flush()
        await self._replace_sources(question.id, request.sources)
        await self.session.flush()
        await self.session.refresh(question)
        response = await self.query_service.to_response(question)
        await self.session.commit()
        return response

    async def update(
        self,
        question_id: int,
        request: AdaptationUpdateRequest,
    ) -> AdaptationResponse:
        """更新改编题与来源引用并提交事务。"""
        question = await self.repository.get_by_id(question_id)
        if question is None:
            raise NotFoundException(f"改编题不存在：ID={question_id}")

        update_data = request.model_dump(exclude_unset=True)
        existing_categories = parse_categories(question.category)
        existing_options = parse_options(question.options)
        new_type = (
            request.question_type.value
            if request.question_type is not None
            else question.question_type
        )
        new_content = request.content if request.content is not None else question.content
        new_options = request.options if "options" in update_data else existing_options
        if new_type == "ESSAY":
            new_options = None
        validate_question_values(new_type, new_content, new_options)

        new_subject_id = (
            request.subject_id if "subject_id" in update_data else question.subject_id
        )
        new_categories = (
            request.category if "category" in update_data else existing_categories
        )
        await self.catalog_read_service.validate_question_scope(
            new_subject_id,
            new_categories,
            existing_subject_id=question.subject_id,
            existing_categories=existing_categories,
        )

        new_title = request.title if "title" in update_data else question.title
        new_number = (
            request.question_number
            if "question_number" in update_data
            else question.question_number
        )
        if (
            new_title is not None
            and new_number is not None
            and (new_title != question.title or new_number != question.question_number)
        ):
            duplicate = await self.query_service.check_duplicate(
                new_title,
                new_number,
                [],
                question_id,
            )
            if duplicate.is_duplicate:
                raise ConflictException(
                    f"改编题已存在：{new_title} 第 {new_number} 题"
                )

        # sources 缺省表示不修改来源，显式传入空数组表示清空来源。
        if "sources" in update_data and request.sources is not None:
            await self._replace_sources(question_id, request.sources)

        if "question_number" in update_data:
            question.question_number = new_number
        if "question_type" in update_data:
            question.question_type = new_type
        if "title" in update_data:
            question.title = new_title
        if "content" in update_data:
            question.content = new_content
        if "options" in update_data or "question_type" in update_data:
            question.options = serialize_options(new_options)
        if "answer" in update_data:
            question.answer = request.answer
        if "category" in update_data or "subject_id" in update_data:
            question.category = serialize_categories(new_categories)
        if "subject_id" in update_data:
            question.subject_id = new_subject_id
        if "difficulty" in update_data:
            question.difficulty = request.difficulty.value if request.difficulty else None

        await self.session.flush()
        await self.session.refresh(question)
        response = await self.query_service.to_response(question)
        await self.session.commit()
        return response

    async def delete(self, question_id: int) -> None:
        """删除改编题并提交事务，来源引用由数据库级联删除。"""
        question = await self.repository.get_by_id(question_id)
        if question is None:
            raise NotFoundException(f"改编题不存在：ID={question_id}")
        await self.session.delete(question)
        await self.session.commit()

    async def _replace_sources(
        self,
        question_id: int | None,
        sources: list[AdaptationSourceRefInput],
    ) -> None:
        """在同一事务内整体替换来源引用，并解析命中的真题 ID。"""
        if question_id is None:
            raise NotFoundException("改编题")
        normalized = self._normalize_sources(sources)

        existing = await self.repository.list_sources({question_id})
        for row in existing:
            await self.session.delete(row)
        if not normalized:
            return
        # 先执行删除再插入：同一批次内插入会先于删除下发，会与旧行触发唯一约束冲突。
        await self.session.flush()

        exam_refs = await self.exam_read_service.resolve_sources(
            {(year, number) for year, number, _ in normalized}
        )
        for year, number, part in normalized:
            exam_ref = exam_refs.get((year, number))
            self.session.add(
                AdaptationSource(
                    adaptation_id=question_id,
                    source_year=year,
                    source_question_number=number,
                    source_part=part,
                    exam_question_id=exam_ref.id if exam_ref else None,
                )
            )

    @staticmethod
    def _normalize_sources(
        sources: list[AdaptationSourceRefInput],
    ) -> list[tuple[int, int, str]]:
        """按输入顺序整理来源三元组，并拒绝同一题内的重复引用。"""
        normalized: list[tuple[int, int, str]] = []
        seen: set[tuple[int, int, str]] = set()
        for item in sources:
            key = (item.source_year, item.source_question_number, item.source_part or "")
            if key in seen:
                raise ValidationException(
                    f"来源引用重复：{key[0]} 年第 {key[1]} 题"
                )
            seen.add(key)
            normalized.append(key)
        return normalized
