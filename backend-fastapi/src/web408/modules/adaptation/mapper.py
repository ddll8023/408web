"""改编题实体到 API 响应的纯转换。"""
from web408.modules.adaptation.models import AdaptationQuestion
from web408.modules.adaptation.schemas import (
    AdaptationResponse,
    AdaptationSourceRefResponse,
)
from web408.modules.question_content.serialization import parse_categories, parse_options


def to_adaptation_response(
    question: AdaptationQuestion,
    *,
    subject_name: str | None,
    author_name: str | None,
    sources: list[AdaptationSourceRefResponse],
    source_summary: str,
) -> AdaptationResponse:
    """将已取得显示字段与来源引用的改编题实体转换为公开响应。"""
    return AdaptationResponse(
        id=question.id,
        title=question.title,
        question_type=question.question_type,
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
        sources=sources,
        source_summary=source_summary,
    )
