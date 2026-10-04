"""从三类详情形成有界文本快照，登记题目图片引用但不读取素材文件。

本模块只做文本解析与引用登记：图片字节由业务层按受控目录读取，本模块不接触文件系统。
"""
from collections.abc import Sequence
from dataclasses import dataclass, replace
from html.parser import HTMLParser
from typing import Final

from markdown_it import MarkdownIt
from markdown_it.token import Token
from pydantic import ValidationError as PydanticValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.config import AiConfig
from web408.core.exceptions import ValidationException
from web408.modules.adaptation.query_service import AdaptationQueryService
from web408.modules.adaptation.schemas import AdaptationResponse
from web408.modules.ai.answer_schemas import AiAnswerSessionCreateRequest, AiAnswerSource
from web408.modules.catalog.read_service import CatalogReadService
from web408.modules.ai.question_images import (
    EXTERNAL_REASON,
    INLINE_REASON,
    OMIT_TEXTS,
    SVG_REASON,
    resolve_local_image,
)
from web408.modules.ai.session_schemas import (
    AiOmittedQuestionImage,
    AiQuestionImageRef,
    AiQuestionSnapshot,
    ImageOmissionReason,
    QuestionKind,
)
from web408.modules.exam.query_service import ExamQueryService
from web408.modules.exam.schemas import ExamResponse
from web408.modules.mock.query_service import MockQueryService
from web408.modules.mock.schemas import MockResponse


# 快照头部固定说明：向模型交代图号语义与参考解析的可靠性，不随题目变化。
SNAPSHOT_HEADER: Final = (
    "当前题目固定文本快照（[图 N] 表示题目第 N 张图，是否附带见会话说明；参考解析不保证正确）："
)


@dataclass(frozen=True, slots=True)
class SnapshotLimits:
    """一次快照渲染的文本与 SVG 预算；图片数量与体积在业务层读取时再限制。"""

    max_bytes: int
    svg_max_bytes: int
    svg_total_max_bytes: int
    keep_svg: bool


def _attribute(attrs: Sequence[tuple[str, str | None]], name: str) -> str | None:
    """按属性名取 HTML 属性值；缺失时返回 None。"""
    for key, value in attrs:
        if key.lower() == name:
            return value
    return None


class TextSnapshotBuilder(HTMLParser):
    """结构化移除图片和非正文 HTML，登记图片引用，保留文字、公式及普通代码。"""

    def __init__(self, limits: SnapshotLimits) -> None:
        """绑定本次渲染预算；图片引用与未附带登记跨字段累积，图号保持连续。"""
        super().__init__(convert_charrefs=True)
        self.limits = limits
        self.parts: list[str] = []
        self.images: list[AiQuestionImageRef] = []
        self.omitted: list[AiOmittedQuestionImage] = []
        self.suppressed_tags: list[str] = []
        self.image_count = 0
        self.svg_bytes = 0

    def omit(self, index: int, reason: ImageOmissionReason) -> None:
        """登记一张未附带图片并写明固定原因；文案不携带文件名以外任何地址信息。"""
        self.omitted.append(AiOmittedQuestionImage(index=index, reason=reason))
        self.parts.append(f"[图 {index}：未附带（{OMIT_TEXTS[reason]}）]")

    def image_placeholder(self, url: str | None, unresolved_reason: ImageOmissionReason) -> None:
        """登记一次图片引用：能映射到本站上传目录就等待业务层读取，否则只留占位说明。"""
        self.image_count += 1
        index = self.image_count
        resolved = resolve_local_image(url) if url else None
        if resolved is None:
            self.omit(index, unresolved_reason)
            return
        filename, media_type = resolved
        self.images.append(AiQuestionImageRef(index=index, filename=filename, media_type=media_type))
        self.parts.append(f"[图 {index}]")

    def svg_block(self, source: str) -> None:
        """内联 SVG 以源码文本进入上下文；超过单块或总量预算时回退为占位。"""
        self.image_count += 1
        index = self.image_count
        size = len(source.encode("utf-8"))
        if (not self.limits.keep_svg or size > self.limits.svg_max_bytes
                or self.svg_bytes + size > self.limits.svg_total_max_bytes):
            self.omit(index, SVG_REASON)
            return
        self.svg_bytes += size
        self.parts.append(f"\n[图 {index} 为 SVG 源码，见下]\n```svg\n{source}\n```\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.suppressed_tags:
            if tag not in {"img", "br", "hr", "input", "meta", "link", "source", "embed"}:
                self.suppressed_tags.append(tag)
            return
        if tag in {"svg", "img", "image"}:
            self.image_placeholder(_attribute(attrs, "src"), INLINE_REASON)
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
        if self.suppressed_tags:
            return
        if tag in {"svg", "img", "image"}:
            self.image_placeholder(_attribute(attrs, "src"), INLINE_REASON)
        elif tag in {"br", "hr"}:
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
                self.image_placeholder(token.attrGet("src"), EXTERNAL_REASON)
            elif token.type == "fence":
                language = token.info.strip().split(maxsplit=1)
                if language and language[0].lower() == "svg":
                    self.svg_block(token.content)
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


def _render_fields(
    fields: Sequence[tuple[str, str]],
    limits: SnapshotLimits,
    header: str = SNAPSHOT_HEADER,
) -> tuple[str, list[AiQuestionImageRef], list[AiOmittedQuestionImage], int]:
    """按给定预算渲染一次完整快照，返回文本、图片引用、未附带登记与 SVG 实际字节。"""
    builder = TextSnapshotBuilder(limits)
    rendered = [f"{label}：\n{builder.convert(value)}" for label, value in fields]
    text = header + "\n\n" + "\n\n".join(rendered)
    return text, builder.images, builder.omitted, builder.svg_bytes


async def read_question(
    session: AsyncSession, kind: QuestionKind, question_id: int,
) -> ExamResponse | MockResponse | AdaptationResponse:
    """读取已保存题目，生成草稿也必须以存在的题目为目标。"""
    question: ExamResponse | MockResponse | AdaptationResponse
    if kind == "exam":
        question = await ExamQueryService(session).get_by_id(question_id)
    elif kind == "mock":
        question = await MockQueryService(session).get_by_id(question_id)
    else:
        question = await AdaptationQueryService(session).get_by_id(question_id)

    return question


async def build_question_snapshot(
    session: AsyncSession, kind: QuestionKind, question_id: int, config: AiConfig,
) -> AiQuestionSnapshot:
    """咨询保留参考解析，生成答案走独立的无参考答案快照。"""
    question = await read_question(session, kind, question_id)
    fields: list[tuple[str, str]] = [
        ("科目", question.subject_name or "未分类"),
        ("分类", "、".join(question.category or [])),
        ("题型", question.question_type.value),
        ("题干", question.content),
    ]
    if question.options is not None:
        fields.extend((f"选项 {letter}", text) for letter, text in question.options.model_dump().items())
    fields.append(("参考答案解析", question.answer or "未提供"))
    return render_question_snapshot(fields, kind, question_id, config)


async def build_answer_snapshot(
    session: AsyncSession, request: AiAnswerSessionCreateRequest, config: AiConfig,
) -> tuple[AiQuestionSnapshot, AiAnswerSource]:
    """固定实际题面与对比基线；只把题面发送给模型，原答案仅返回浏览器。"""
    question = await read_question(session, request.question_kind, request.question_id)
    if request.draft is not None:
        source = AiAnswerSource(**request.draft.model_dump(), answer=None)
    else:
        values = [question.content]
        if question.options is not None:
            values.extend(question.options.model_dump().values())
        ensure_text_budget(values, config.question_text_max_bytes)
        try:
            source = AiAnswerSource(
                question_type=question.question_type.value, subject_id=question.subject_id,
                content=question.content, options=question.options, answer=question.answer,
            )
        except PydanticValidationError:
            raise ValidationException("已保存题面不完整，请在编辑框修正后生成") from None
    subject_name = await CatalogReadService(session).get_subject_name(source.subject_id)
    if source.subject_id is not None and subject_name is None:
        raise ValidationException("草稿科目不存在，请重新选择")
    fields: list[tuple[str, str]] = [
        ("科目", subject_name or "未分类"),
        ("题型", source.question_type),
        ("题干", source.content),
    ]
    if source.options is not None:
        fields.extend((f"选项 {letter}", text) for letter, text in source.options.model_dump().items())
    snapshot = render_question_snapshot(
        fields, request.question_kind, request.question_id, config, answer_generation=True,
    )
    return snapshot, source


def render_question_snapshot(
    fields: Sequence[tuple[str, str]], kind: QuestionKind, question_id: int, config: AiConfig,
    *, answer_generation: bool = False,
) -> AiQuestionSnapshot:
    """咨询与生成共用文本和图片预算，不截断题面，也不额外读取文件。"""
    ensure_text_budget([value for _, value in fields], config.question_text_max_bytes)

    limits = SnapshotLimits(
        max_bytes=config.question_text_max_bytes,
        svg_max_bytes=config.question_svg_max_bytes,
        svg_total_max_bytes=config.question_svg_total_max_bytes,
        keep_svg=True,
    )
    header = (
        "当前题目固定题面（不含原答案；[图 N] 表示第 N 张图，是否附带见会话说明）："
        if answer_generation else SNAPSHOT_HEADER
    )
    text, images, omitted, svg_bytes = _render_fields(fields, limits, header)
    if svg_bytes and len(text.encode("utf-8")) > limits.max_bytes:
        # SVG 源码把快照顶出文本上限时整体回退为占位，保证改动前可用的题目仍可咨询。
        text, images, omitted, _ = _render_fields(fields, replace(limits, keep_svg=False), header)
    ensure_text_budget([text], config.question_text_max_bytes)
    return AiQuestionSnapshot(
        question_kind=kind,
        question_id=question_id,
        text=text,
        images=tuple(images),
        omitted=tuple(omitted),
    )
