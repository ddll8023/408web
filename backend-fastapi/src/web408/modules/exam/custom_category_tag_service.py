"""真题自定义分类标签的写入边界。

题目按自定义分类名称保存标签，自定义分类用例重命名分类后需要同步真题中的旧名称。
本模块只访问真题表，不依赖自定义分类模块。
"""
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.exam.repository import ExamRepository
from web408.modules.question_content.serialization import replace_category_name


class ExamCustomCategoryTagService:
    """向自定义分类用例提供真题标签改名，复用调用方会话且不提交事务。"""

    def __init__(self, session: AsyncSession) -> None:
        """绑定真题持久化边界。"""
        self.repository = ExamRepository(session)

    async def rename_category(
        self,
        subject_id: int,
        old_name: str,
        new_name: str,
    ) -> int:
        """把科目下真题的旧自定义分类名称改为新名称，返回被更新的题目数。"""
        questions = await self.repository.list_by_custom_category_tag(
            subject_id,
            old_name,
        )
        updated = 0
        for question in questions:
            replaced = replace_category_name(
                question.custom_category,
                old_name,
                new_name,
            )
            if replaced is None:
                continue
            question.custom_category = replaced
            updated += 1
        return updated
