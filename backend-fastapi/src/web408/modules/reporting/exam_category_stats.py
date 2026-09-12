"""真题分类统计的共享聚合规则。"""
from dataclasses import dataclass, field
from typing import Iterable

from web408.modules.catalog.read_service import CatalogCategoryRead
from web408.modules.exam.query_service import ExamCategoryQuestionRead
from web408.modules.question_content.serialization import parse_categories


_UNFILED_ORDER = 2_147_483_647


@dataclass(slots=True)
class QuestionStats:
    """按题目 ID 去重的题型统计。"""

    question_ids: set[int] = field(default_factory=set)
    choice_ids: set[int] = field(default_factory=set)
    subjective_ids: set[int] = field(default_factory=set)

    @property
    def count(self) -> int:
        """返回去重后的题目数量。"""
        return len(self.question_ids)

    @property
    def choice_count(self) -> int:
        """返回去重后的选择题数量。"""
        return len(self.choice_ids)

    @property
    def subjective_count(self) -> int:
        """返回去重后的主观题数量。"""
        return len(self.subjective_ids)

    def add(self, question: ExamCategoryQuestionRead) -> None:
        """把一道题加入统计，并按题型归类。"""
        self.question_ids.add(question.id)
        if question.question_type == "CHOICE":
            self.choice_ids.add(question.id)
        else:
            self.subjective_ids.add(question.id)

    def merge(self, other: "QuestionStats") -> None:
        """合并另一组去重统计。"""
        self.question_ids.update(other.question_ids)
        self.choice_ids.update(other.choice_ids)
        self.subjective_ids.update(other.subjective_ids)

    def copy(self) -> "QuestionStats":
        """复制统计集合，避免父节点聚合修改子节点数据。"""
        return QuestionStats(
            question_ids=set(self.question_ids),
            choice_ids=set(self.choice_ids),
            subjective_ids=set(self.subjective_ids),
        )


@dataclass(slots=True)
class CategoryStatsNode:
    """分类树中的统计节点。"""

    category_id: int | None
    parent_id: int | None
    name: str
    order_num: int
    enabled: bool
    direct: QuestionStats = field(default_factory=QuestionStats)
    subtree: QuestionStats = field(default_factory=QuestionStats)
    children: list["CategoryStatsNode"] = field(default_factory=list)
    is_unfiled: bool = False


@dataclass(slots=True)
class SubjectCategoryStats:
    """单个科目的分类统计结果。"""

    subject_id: int | None
    subject_name: str
    categories: list[CategoryStatsNode]
    categorized: QuestionStats
    category_reference_count: int
    invalid_question_ids: list[int]


def build_subject_category_stats(
    questions: Iterable[ExamCategoryQuestionRead],
    categories: Iterable[CatalogCategoryRead],
    *,
    subject_id: int | None,
    subject_name: str,
) -> SubjectCategoryStats:
    """按目录树构建一个科目的分类统计结果。

    题目仍以分类名称 JSON 保存，因此先按名称形成直接统计，再映射到目录节点；
    未出现在目录中的标签会被放入虚拟的“未归档分类”节点。
    """
    label_stats: dict[str, QuestionStats] = {}
    categorized = QuestionStats()
    invalid_question_ids: list[int] = []
    category_reference_count = 0

    for question in questions:
        parsed_categories = parse_categories(question.category)
        if parsed_categories is None:
            if question.category:
                invalid_question_ids.append(question.id)
            continue

        unique_categories = list(
            dict.fromkeys(
                category.strip()
                for category in parsed_categories
                if category.strip()
            )
        )
        if not unique_categories:
            continue

        categorized.add(question)
        category_reference_count += len(unique_categories)
        for category_name in unique_categories:
            label_stats.setdefault(category_name, QuestionStats()).add(question)

    category_nodes: dict[int, CategoryStatsNode] = {}
    category_list = list(categories)
    for category in category_list:
        if category.id is None:
            continue
        direct = label_stats.get(category.name, QuestionStats()).copy()
        category_nodes[category.id] = CategoryStatsNode(
            category_id=category.id,
            parent_id=category.parent_id,
            name=category.name,
            order_num=category.order_num,
            enabled=category.enabled,
            direct=direct,
        )

    children_by_parent: dict[int, list[CategoryStatsNode]] = {}
    roots: list[CategoryStatsNode] = []
    for node in category_nodes.values():
        if node.parent_id is not None and node.parent_id in category_nodes:
            children_by_parent.setdefault(node.parent_id, []).append(node)
        else:
            roots.append(node)

    for children in children_by_parent.values():
        children.sort(key=_node_sort_key)

    roots.sort(key=_node_sort_key)
    for root in roots:
        _calculate_subtree(root, children_by_parent)

    known_names = {category.name for category in category_list}
    unfiled_names = sorted(name for name in label_stats if name not in known_names)
    if unfiled_names:
        unfiled_children = [
            CategoryStatsNode(
                category_id=None,
                parent_id=None,
                name=name,
                order_num=index,
                enabled=True,
                direct=label_stats[name].copy(),
                is_unfiled=True,
            )
            for index, name in enumerate(unfiled_names)
        ]
        unfiled = CategoryStatsNode(
            category_id=None,
            parent_id=None,
            name="未归档分类",
            order_num=_UNFILED_ORDER,
            enabled=True,
            children=unfiled_children,
            is_unfiled=True,
        )
        _calculate_subtree(unfiled, {})
        roots.append(unfiled)

    return SubjectCategoryStats(
        subject_id=subject_id,
        subject_name=subject_name,
        categories=roots,
        categorized=categorized,
        category_reference_count=category_reference_count,
        invalid_question_ids=invalid_question_ids,
    )


def _calculate_subtree(
    node: CategoryStatsNode,
    children_by_parent: dict[int, list[CategoryStatsNode]],
) -> None:
    """递归计算节点及其后代的题目 ID 并集。"""
    parent_key = node.category_id if node.category_id is not None else -1
    node.children = children_by_parent.get(parent_key, node.children)
    node.subtree = node.direct.copy()
    for child in node.children:
        _calculate_subtree(child, children_by_parent)
        node.subtree.merge(child.subtree)


def _node_sort_key(node: CategoryStatsNode) -> tuple[int, int]:
    """按目录手工顺序和稳定 ID 排序。"""
    return node.order_num, node.category_id if node.category_id is not None else 0
