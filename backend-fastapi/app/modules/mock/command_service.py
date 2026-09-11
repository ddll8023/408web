"""模拟题写入用例。"""
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.modules.mock.models import MockQuestion
from app.modules.catalog.read_service import CatalogReadService
from app.modules.mock.query_service import MockQueryService
from app.modules.mock.repository import MockRepository
from app.modules.mock.schemas import MockCreateRequest, MockResponse, MockUpdateRequest
from app.modules.question_content.serialization import (
    parse_categories,
    parse_options,
    serialize_categories,
    serialize_options,
)
from app.modules.question_content.validation import validate_question_values


class MockCommandService:
    """编排模拟题新增、更新和删除。"""

    def __init__(self, session: AsyncSession, query_service: MockQueryService) -> None:
        self.session = session
        self.repository = MockRepository(session)
        self.query_service = query_service
        self.catalog_read_service = CatalogReadService(session)

    async def create(self, request: MockCreateRequest, author_id: int) -> MockResponse:
        """创建模拟题并提交事务。"""
        validate_question_values(request.question_type, request.content, request.options)
        await self.catalog_read_service.validate_question_scope(
            request.subject_id,
            request.category,
        )
        duplicate = await self.query_service.check_duplicate(
            request.source,
            request.title,
            request.question_number,
        )
        if duplicate.is_duplicate:
            raise ConflictException("相同来源、标题和题号的模拟题已存在")

        question = MockQuestion(
            source=request.source,
            question_number=request.question_number,
            question_type=request.question_type.value,
            title=request.title,
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
        await self.session.refresh(question)
        response = await self.query_service.to_response(question)
        await self.session.commit()
        return response

    async def update(
        self,
        question_id: int,
        request: MockUpdateRequest,
    ) -> MockResponse:
        """更新模拟题并提交事务。"""
        question = await self.repository.get_by_id(question_id)
        if question is None:
            raise NotFoundException(f"模拟题不存在：ID={question_id}")

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

        new_source = request.source if "source" in update_data else question.source
        if not new_source or not new_source.strip():
            raise ValidationException("来源机构不能为空")
        new_title = request.title if "title" in update_data else question.title
        new_number = (
            request.question_number
            if "question_number" in update_data
            else question.question_number
        )
        if (
            new_title is not None
            and new_number is not None
            and (
                new_source != question.source
                or new_title != question.title
                or new_number != question.question_number
            )
        ):
            duplicate = await self.query_service.check_duplicate(
                new_source,
                new_title,
                new_number,
                question_id,
            )
            if duplicate.is_duplicate:
                raise ConflictException("相同来源、标题和题号的模拟题已存在")

        if "source" in update_data:
            question.source = new_source
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
        """删除模拟题并提交事务。"""
        question = await self.repository.get_by_id(question_id)
        if question is None:
            raise NotFoundException(f"模拟题不存在：ID={question_id}")
        await self.session.delete(question)
        await self.session.commit()
