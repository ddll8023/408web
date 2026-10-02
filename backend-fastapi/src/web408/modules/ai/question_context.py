"""从三类详情形成有界文本快照，忽略图片载荷和个人信息，不访问素材文件。"""
from html.parser import HTMLParser

from markdown_it import MarkdownIt
from markdown_it.token import Token
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.exceptions import ValidationException
from web408.modules.adaptation.query_service import AdaptationQueryService
from web408.modules.adaptation.schemas import AdaptationResponse
from web408.modules.ai.session_schemas import AiQuestionSnapshot, QuestionKind
from web408.modules.exam.query_service import ExamQueryService
from web408.modules.exam.schemas import ExamResponse
from web408.modules.mock.query_service import MockQueryService
from web408.modules.mock.schemas import MockResponse


class TextSnapshotBuilder(HTMLParser):
    """结构化移除图像和非正文 HTML，保留文字、公式及普通代码。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.omitted_images = 0
        self.suppressed_tags: list[str] = []

    def image_placeholder(self) -> None:
        self.omitted_images += 1
        self.parts.append(f"[图 {self.omitted_images}：纯文本咨询未提供]")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.suppressed_tags:
            if tag not in {"img", "br", "hr", "input", "meta", "link", "source", "embed"}:
                self.suppressed_tags.append(tag)
            return
        if tag in {"svg", "img", "image"}:
            self.image_placeholder()
        if tag in {"svg", "script", "style", "iframe", "object", "video"}:
            self.suppressed_tags.append(tag)
        elif tag in {"br", "p", "div", "li", "tr"}:
            self.parts.append("\n")
        elif tag in {"td", "th"}:
            self.parts.append("\t")

    def handle_endtag(self, tag: str) -> None:
        if self.suppressed_tags:
            if tag in self.suppressed_tags:
                index = len(self.suppressed_tags) - 1 - self.suppressed_tags[::-1].index(tag)
                del self.suppressed_tags[index:]
            return
        if tag in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self.suppressed_tags and tag in {"svg", "img", "image"}:
            self.image_placeholder()
        elif not self.suppressed_tags and tag in {"br", "hr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.suppressed_tags:
            self.parts.append(data)

    def append_tokens(self, tokens: list[Token]) -> None:
        for token in tokens:
            if token.type in {"html_inline", "html_block"}:
                self.feed(token.content)
            elif self.suppressed_tags:
                continue
            elif token.type == "image":
                self.image_placeholder()
            elif token.type == "fence":
                language = token.info.strip().split(maxsplit=1)
                if language and language[0].lower() == "svg":
                    self.image_placeholder()
                else:
                    self.parts.append(f"\n{token.content}\n")
            elif token.children:
                self.append_tokens(token.children)
            elif token.type in {"text", "code_inline", "code_block"}:
                self.parts.append(token.content)
            elif token.type in {"softbreak", "hardbreak"} or token.block:
                self.parts.append("\n")

    def convert(self, source: str) -> str:
        # 每个业务字段独立解析，未闭合 HTML 不得吞掉后续参考解析。
        self.suppressed_tags.clear()
        self.reset()
        self.parts.clear()
        # 保留 LaTeX 的反斜杠、下划线和星号，不按普通 Markdown 转义或强调改写公式。
        parser = MarkdownIt("commonmark", {"html": True}).disable(["escape", "emphasis"])
        self.append_tokens(parser.parse(source))
        self.close()
        return "".join(self.parts).strip()


def ensure_text_budget(values: list[str], max_bytes: int) -> None:
    """解析前先限制原文，解析后再限制快照；超限不静默截断。"""
    total = 0
    try:
        for value in values:
            if len(value) > max_bytes:
                raise ValidationException("题目文本超过咨询上限，请缩小内容后重新咨询")
            total += len(value.encode("utf-8"))
            if total > max_bytes:
                raise ValidationException("题目文本超过咨询上限，请缩小内容后重新咨询")
    except UnicodeError:
        raise ValidationException("题目包含无效 Unicode 字符，无法创建咨询快照") from None


async def build_question_snapshot(
    session: AsyncSession,
    kind: QuestionKind,
    question_id: int,
    max_bytes: int,
) -> AiQuestionSnapshot:
    """复用详情查询，只选择题型、题干、选项、参考解析和目录信息。"""
    question: ExamResponse | MockResponse | AdaptationResponse
    if kind == "exam":
        question = await ExamQueryService(session).get_by_id(question_id)
    elif kind == "mock":
        question = await MockQueryService(session).get_by_id(question_id)
    else:
        question = await AdaptationQueryService(session).get_by_id(question_id)

    fields: list[tuple[str, str]] = [
        ("科目", question.subject_name or "未分类"),
        ("分类", "、".join(question.category or [])),
        ("题型", question.question_type.value),
        ("题干", question.content),
    ]
    if question.options is not None:
        fields.extend((f"选项 {letter}", text) for letter, text in question.options.model_dump().items())
    fields.append(("参考答案解析", question.answer or "未提供"))
    ensure_text_budget([value for _, value in fields], max_bytes)
    builder = TextSnapshotBuilder()
    rendered = [f"{label}：\n{builder.convert(value)}" for label, value in fields]
    text = "当前题目固定文本快照（图片未提供，参考解析不保证正确）：\n\n" + "\n\n".join(rendered)
    ensure_text_budget([text], max_bytes)
    return AiQuestionSnapshot(
        question_kind=kind,
        question_id=question_id,
        text=text,
        omitted_images=builder.omitted_images,
    )
