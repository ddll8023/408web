"""真题实体到 API 响应的纯转换。"""
from web408.modules.exam.models import ExamQuestion
from web408.modules.exam.schemas import ExamResponse
from web408.modules.question_content.serialization import parse_categories, parse_options


def to_exam_response(
    question: ExamQuestion,
    *,
    subject_name: str | None,
    author_name: str | None,
) -> ExamResponse:
    """将已取得显示字段的真题实体转换为公开响应。"""
    return ExamResponse(
        id=question.id,
        year=question.year,
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
