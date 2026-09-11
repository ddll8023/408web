"""分类层级编码生成工具。"""
from collections import Counter
from collections.abc import Iterable, Sequence
import re

from app.modules.catalog.models import ExamCategory


# GB2312 编码对应的拼音首字母区间。使用标准库即可完成常用中文名称转换，
# 避免为分类编码引入额外运行时依赖。
_PINYIN_RANGES: tuple[tuple[int, int, str], ...] = (
    (45217, 45252, "a"),
    (45253, 45760, "b"),
    (45761, 46317, "c"),
    (46318, 46825, "d"),
    (46826, 47009, "e"),
    (47010, 47296, "f"),
    (47297, 47613, "g"),
    (47614, 48118, "h"),
    (48119, 49061, "j"),
    (49062, 49323, "k"),
    (49324, 49895, "l"),
    (49896, 50370, "m"),
    (50371, 50613, "n"),
    (50614, 50621, "o"),
    (50622, 50905, "p"),
    (50906, 51386, "q"),
    (51387, 51445, "r"),
    (51446, 52217, "s"),
    (52218, 52697, "t"),
    (52698, 52979, "w"),
    (52980, 53688, "x"),
    (53689, 54480, "y"),
    (54481, 55289, "z"),
)
_SEQUENCE_PATTERN = re.compile(r"(?:^|-)(\d+)-[a-z0-9]+(?=-|$)")
_PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9]*$")


def pinyin_initials(value: str) -> str:
    """返回名称的拼音首字母或 ASCII 字符串。"""
    initials: list[str] = []
    for char in value.strip():
        if char.isspace() or not char.isalnum():
            continue
        if char.isascii():
            initials.append(char.lower())
            continue
        try:
            encoded = char.encode("gb2312")
        except UnicodeEncodeError:
            # 极少数 GB2312 未覆盖的字符不参与编码，避免生成不可读的乱码。
            continue
        if len(encoded) != 2:
            continue
        code = encoded[0] * 256 + encoded[1]
        for lower, upper, initial in _PINYIN_RANGES:
            if lower <= code <= upper:
                initials.append(initial)
                break
    return "".join(initials) or "category"


def subject_code_prefix(
    categories: Iterable[ExamCategory],
    subject_name: str,
) -> str:
    """优先沿用当前科目已有前缀，没有时按科目名称生成。"""
    prefixes: Counter[str] = Counter()
    for category in categories:
        prefix = category.code.split("-", 1)[0].lower()
        if prefix != "cat" and _PREFIX_PATTERN.fullmatch(prefix):
            prefixes[prefix] += 1
    if prefixes:
        return prefixes.most_common(1)[0][0]
    return pinyin_initials(subject_name)


def extract_last_sequence(code: str) -> int | None:
    """提取层级编码最后一级的数字。"""
    matches = _SEQUENCE_PATTERN.findall(code.lower())
    return int(matches[-1]) if matches else None


def next_sibling_sequence(
    categories: Iterable[ExamCategory],
    parent_id: int | None,
) -> int:
    """返回同一父分类下的新编号。"""
    used = {
        sequence
        for category in categories
        if category.parent_id == parent_id
        for sequence in [extract_last_sequence(category.code)]
        if sequence is not None
    }
    return max(used, default=0) + 1


def build_category_code(
    subject_prefix: str,
    parent_code: str | None,
    sequence: int,
    name: str,
) -> str:
    """按父级路径、同级编号和名称首字母生成分类编码。"""
    segment = f"{sequence:02d}-{pinyin_initials(name)}"
    return f"{parent_code}-{segment}" if parent_code else f"{subject_prefix}-{segment}"


def rebuild_subtree_codes(
    categories: Sequence[ExamCategory],
    root_id: int,
    subject_prefix: str,
) -> dict[int, str]:
    """父分类变化后，重建指定子树的层级编码。"""
    by_id = {category.id: category for category in categories}
    root = by_id.get(root_id)
    if root is None:
        return {}

    children_by_parent: dict[int | None, list[ExamCategory]] = {}
    for category in categories:
        children_by_parent.setdefault(category.parent_id, []).append(category)
    for children in children_by_parent.values():
        children.sort(key=lambda item: (item.order_num, item.id or 0))

    codes: dict[int, str] = {}

    def assign_children(
        parent: ExamCategory,
        parent_code: str,
    ) -> None:
        children = children_by_parent.get(parent.id, [])
        assigned: set[int] = set()
        next_sequence = 1
        for child in children:
            sequence = extract_last_sequence(child.code)
            if sequence is None or sequence in assigned:
                while next_sequence in assigned:
                    next_sequence += 1
                sequence = next_sequence
            assigned.add(sequence)
            next_sequence = max(next_sequence, sequence + 1)
            child_code = build_category_code(
                subject_prefix,
                parent_code,
                sequence,
                child.name,
            )
            codes[child.id] = child_code
            assign_children(child, child_code)

    parent_code = by_id[root.parent_id].code if root.parent_id in by_id else None
    external_siblings = [
        category
        for category in children_by_parent.get(root.parent_id, [])
        if category.id != root.id
    ]
    used_by_siblings = {
        sequence
        for category in external_siblings
        for sequence in [extract_last_sequence(category.code)]
        if sequence is not None
    }
    root_sequence = extract_last_sequence(root.code)
    if root_sequence is None or root_sequence in used_by_siblings:
        root_sequence = max(used_by_siblings, default=0) + 1
    root_code = build_category_code(
        subject_prefix,
        parent_code,
        root_sequence,
        root.name,
    )
    codes[root.id] = root_code
    assign_children(root, root_code)
    return codes
