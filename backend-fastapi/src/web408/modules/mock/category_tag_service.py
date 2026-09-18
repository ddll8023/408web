"""模拟题分类标签的写入边界。

题目按分类名称保存标签，目录用例重命名分类后需要同步模拟题中的旧名称。
本模块只访问模拟题表，不依赖目录模块。
"""
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.mock.repository import MockRepository
from web408.modules.question_content.serialization import replace_category_name


class MockCategoryTagService:
    """向目录用例提供模拟题分类标签改名，复用调用方会话且不提交事务。"""

    def __init__(self, session: AsyncSession) -> None:
        """绑定模拟题持久化边界。"""
        self.repository = MockRepository(session)

    async def rename_category(
        self,
        subject_id: int,
        old_name: str,
        new_name: str,
    ) -> int:
        """把科目下模拟题的旧分类名称改为新名称，返回被更新的题目数。"""
        questions = await self.repository.list_by_category_tag(subject_id, old_name)
        updated = 0
        for question in questions:
            replaced = replace_category_name(question.category, old_name, new_name)
            if replaced is None:
                continue
            question.category = replaced
            updated += 1
        return updated
