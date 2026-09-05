"""真题和模拟题共用的数据转换。"""
import json
from json import JSONDecodeError
from typing import Optional

from pydantic import ValidationError

from app.schemas.question import QuestionOptions


def serialize_options(options: Optional[QuestionOptions]) -> Optional[str]:
    """将选择题选项序列化为数据库 JSON 文本。"""
    if options is None:
        return None
    return json.dumps(options.model_dump(), ensure_ascii=False)


def serialize_categories(categories: Optional[list[str]]) -> Optional[str]:
    """将分类名称列表序列化为数据库 JSON 文本。"""
    if not categories:
        return None
    return json.dumps(categories, ensure_ascii=False)


def parse_options(value: Optional[str]) -> Optional[QuestionOptions]:
    """将数据库中的选项 JSON 转换为响应模型。"""
    if not value:
        return None
    try:
        return QuestionOptions.model_validate(json.loads(value))
    except (JSONDecodeError, TypeError, ValidationError):
        return None


def parse_categories(value: Optional[str]) -> Optional[list[str]]:
    """将数据库中的分类 JSON 转换为列表。"""
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except (JSONDecodeError, TypeError):
        return None
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        return None
    return parsed
