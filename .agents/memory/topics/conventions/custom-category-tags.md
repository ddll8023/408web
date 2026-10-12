# 自定义分类标签（题目挂载口径）

### 标签以名称为持久标识

约定：真题通过 `exam_question.custom_category` 保存自定义分类**名称**（JSON 数组），不是分类 ID。名称在同一科目内唯一；分类改名时由 `ExamCustomCategoryTagService` 同步已打标真题的旧名称，移动分类不影响标签。

适用：`backend-fastapi/src/web408/modules/exam/`（字段、筛选、改名同步）与 `modules/custom_category/`（改名、删除保护）。

原因：三类题目的既有分类标签同样按名称保存，沿用同一口径可复用序列化、LIKE 筛选、分组与改名同步；改用 ID 需要额外的关联表和 JOIN 查询。

### 删除分类前必须先摘掉题目标签

约定：删除自定义分类时，若存在子分类或仍有真题引用该名称，接口直接拒绝并返回引用数（`ExamReadService.count_custom_category_references`）；要删除需先在题目上摘掉标签。

适用：`backend-fastapi/src/web408/modules/custom_category/command_service.py` 的删除用例。

原因：标签是名称而非外键，数据库不会级联清理；直接删除会让真题留下指向不存在分类的名称，只能靠前端分组兜底。

### 按名称筛选必须带 subject_id

约定：名称唯一性只在科目内成立，按自定义分类名称筛选的查询必须带 `subject_id`；`ExamQueryService` 在科目已知时把所选节点展开为其启用子树的名称集合，再下推为名称条件。

适用：`backend-fastapi/src/web408/modules/exam/query_service.py`、`modules/exam/repository.py` 的名称条件构造。

原因：缺少科目维度时不同科目的同名分类会互相命中；科目未知时只能退化为单名称匹配。
