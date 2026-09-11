"""模拟题实体到 API 响应的纯转换。"""
from app.modules.mock.models import MockQuestion
from app.modules.mock.schemas import MockResponse
from app.modules.question_content.serialization import parse_categories, parse_options


def to_mock_response(
    question: MockQuestion,
    *,
    subject_name: str | None,
    author_name: str | None,
) -> MockResponse:
    """将已取得显示字段的模拟题实体转换为公开响应。"""
    return MockResponse(
        id=question.id,
        source=question.source,
        question_number=question.question_number,
        question_type=question.question_type,
        title=question.title,
        content=question.content,
        options=parse_options(question.options),
        answer=question.answer,
        category=parse_categories(question.category),
        subject_id=question.subject_id,
        subject_name=subject_name,
        difficulty=question.difficulty,
        author_id=question.author_id,
        author_name=author_name,
        create_time=question.create_time.isoformat() if question.create_time else None,
        update_time=question.update_time.isoformat() if question.update_time else None,
    )
