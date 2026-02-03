# API 接口文档

**Base URL**: `/api`

本文档根据后端 Controller 源码自动生成，涵盖认证、章节、真题分类、真题、文件上传、模拟题及科目管理等模块。

---

## 1. 认证管理 (Auth)
**Controller**: `AuthController`
**Path**: `/api/auth`

| 接口名称 | HTTP 方法 | 路径 | 权限 | 描述 | 参数 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 用户注册 | POST | `/register` | 公开 | 新用户注册接口 | Body: `RegisterDTO` (用户名, 密码等) |
| 用户登录 | POST | `/login` | 公开 | 用户登录接口，返回JWT Token | Body: `LoginDTO` (用户名, 密码) |

---

## 2. 章节管理 (Chapter)
**Controller**: `ChapterController`
**Path**: `/api/chapter`

| 接口名称 | HTTP 方法 | 路径 | 权限 | 描述 | 参数 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 查询启用章节树 | GET | `/subject/{subjectId}` | 公开 | 根据科目ID查询启用章节（树形） | Path: `subjectId` |
| 查询所有章节树 | GET | `/subject/{subjectId}/all` | ADMIN | 根据科目ID查询所有章节（含禁用） | Path: `subjectId` |
| 查询章节详情 | GET | `/{id}` | 公开 | 根据ID查询章节详情 | Path: `id` |
| 创建章节 | POST | `/` | ADMIN | 创建新章节 | Body: `ChapterDTO` |
| 更新章节 | POST | `/{id}` | ADMIN | 更新章节信息 | Path: `id`, Body: `ChapterDTO` |
| 删除章节 | POST | `/{id}/delete` | ADMIN | 删除指定章节 | Path: `id` |

---

## 3. 分类标签管理 (ExamCategory)
**Controller**: `ExamCategoryController`
**Path**: `/api/exam-category`

| 接口名称 | HTTP 方法 | 路径 | 权限 | 描述 | 参数 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 查询所有分类 | GET | `/` | 公开 | 查询所有分类（含统计） | Query: `questionType` (exam/mock/exercise, default: exam) |
| 按科目查询分类 | GET | `/subject/{subjectId}` | 公开 | 按科目查询所有分类 | Path: `subjectId`, Query: `questionType` |
| 查询启用分类 | GET | `/subject/{subjectId}/enabled` | 公开 | 按科目查询启用的分类列表 | Path: `subjectId` |
| 查询分类树 | GET | `/subject/{subjectId}/tree` | 公开 | 按科目查询分类树形结构 | Path: `subjectId` |
| 查询启用分类树 | GET | `/subject/{subjectId}/tree/enabled` | 公开 | 按科目查询启用分类树 | Path: `subjectId` |
| 查询启用分类树(带统计) | GET | `/subject/{subjectId}/tree/enabled/{questionType}` | 公开 | 按科目和题型查询启用分类树 | Path: `subjectId`, `questionType` |
| 查询可选父分类 | GET | `/available-parents` | ADMIN | 查询可作为父分类的列表 | Query: `subjectId`, `excludeId` |
| 查询分类详情 | GET | `/{id}` | 公开 | 根据ID查询分类详情 | Path: `id` |
| 创建分类 | POST | `/` | ADMIN | 创建新分类 | Body: `ExamCategoryDTO` |
| 更新分类 | POST | `/{id}` | ADMIN | 更新分类信息 | Path: `id`, Body: `ExamCategoryDTO` |
| 删除分类 | POST | `/{id}/delete` | ADMIN | 删除指定分类 | Path: `id` |
| 检查分类引用 | GET | `/{id}/usage` | ADMIN | 检查分类是否被引用 | Path: `id` |
| 获取分类统计 | GET | `/stats` | 公开 | 获取各科目去重后的题目数统计 | Query: `questionType` |

---

## 4. 真题管理 (Exam)
**Controller**: `ExamController`
**Path**: `/api/exam`

| 接口名称 | HTTP 方法 | 路径 | 权限 | 描述 | 参数 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 分页查询真题 | GET | `/` | 公开 | 多条件筛选查询真题 | Query: `ExamQueryDTO` (page, size, year, category, subjectId, keyword, etc.) |
| 查询真题详情 | GET | `/{id}` | 公开 | 根据ID查询真题详情 | Path: `id` |
| 检查真题重复 | GET | `/check-duplicate` | ADMIN | 检查年份和题号是否重复 | Query: `year`, `questionNumber` |
| 创建真题 | POST | `/` | ADMIN | 创建新真题 | Body: `ExamQuestionCreateDTO` |
| 更新真题 | POST | `/{id}` | ADMIN | 更新真题信息 | Path: `id`, Body: `ExamQuestionUpdateDTO` |
| 删除真题 | POST | `/{id}/delete` | ADMIN | 删除真题 | Path: `id` |
| 按年份查询 | GET | `/year/{year}` | 公开 | 查询指定年份真题 | Path: `year`, Query: `category`, `subjectId` |
| 查询科目下分类 | GET | `/categories/{subjectId}` | 公开 | 查询科目下有真题的分类名列表 | Path: `subjectId` |
| 查询年份统计 | GET | `/year-stats` | 公开 | 按年份统计真题数量 | Query: `category` |
| 查询真题索引 | GET | `/index` | 公开 | 查询用于年份导航的索引数据 | Query: `category` |
| 查询分类统计 | GET | `/category-stats` | 公开 | 按分类统计真题数量 | Query: `subjectId` |
| 按科目分类查询 | GET | `/by-category` | 公开 | 查询指定科目和分类的真题 | Query: `subjectId`, `category` |
| 导出真题 | GET | `/export` | 公开 | 按科目导出真题 (Markdown) | Query: `subjectId`, `format` |

---

## 5. 文件上传 (FileUpload)
**Controller**: `FileUploadController`
**Path**: `/api/upload`

| 接口名称 | HTTP 方法 | 路径 | 权限 | 描述 | 参数 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 上传图片 | POST | `/image` | 公开 | 上传图片文件 | Form: `file` |
| 查询已上传图片 | GET | `/images` | ADMIN | 列出uploads/images目录下的图片 | Query: `onlyUnreferenced` (bool) |
| 清理未引用图片 | POST | `/images/cleanup` | ADMIN | 删除所有未被真题引用的图片 | - |
| 删除图片 | POST | `/image/delete` | ADMIN | 根据文件名删除图片 | Query: `filename` |

---

## 6. 模拟题管理 (MockQuestion)
**Controller**: `MockQuestionController`
**Path**: `/api/mock`

| 接口名称 | HTTP 方法 | 路径 | 权限 | 描述 | 参数 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 创建模拟题 | POST | `/` | ADMIN | 创建模拟题 | Body: `MockQuestionCreateDTO` |
| 查询模拟题详情 | GET | `/{id}` | 公开 | 根据ID查询模拟题 | Path: `id` |
| 更新模拟题 | POST | `/{id}` | ADMIN | 更新模拟题信息 | Path: `id`, Body: `MockQuestionUpdateDTO` |
| 删除模拟题 | POST | `/{id}/delete` | ADMIN | 删除模拟题 | Path: `id` |
| 分页查询模拟题 | GET | `/` | 公开 | 多条件筛选查询 | Query: page, size, source, category, subjectId, keyword, etc. |
| 按来源查询 | GET | `/source/{source}` | 公开 | 查询指定来源机构的模拟题 | Path: `source`, Query: `category`, `subjectId` |
| 查询来源统计 | GET | `/source-stats` | 公开 | 按来源机构统计数量 | Query: `category` |
| 查询所有来源 | GET | `/sources` | 公开 | 获取所有来源机构列表 | - |
| 查询科目下分类 | GET | `/categories/{subjectId}` | 公开 | 查询科目下有模拟题的分类列表 | Path: `subjectId` |
| 查询科目分类(统计) | GET | `/category-stats/{subjectId}` | 公开 | 查询科目下分类列表及题目数 | Path: `subjectId` |
| 按科目统计 | GET | `/subject-stats` | 公开 | 按科目统计模拟题数量 | - |
| 按来源查询标题 | GET | `/titles/{source}` | 公开 | 获取来源下不重复标题列表 | Path: `source` |

---

## 7. 科目管理 (Subject)
**Controller**: `SubjectController`
**Path**: `/api/subject`

| 接口名称 | HTTP 方法 | 路径 | 权限 | 描述 | 参数 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 查询启用科目 | GET | `/` | 公开 | 查询所有启用状态的科目 | - |
| 查询所有科目 | GET | `/all` | ADMIN | 查询所有科目（含禁用） | - |
| 查询科目详情 | GET | `/{id}` | 公开 | 根据ID查询科目详情 | Path: `id` |
| 按编码查询 | GET | `/code/{code}` | 公开 | 根据编码查询科目 | Path: `code` |
| 创建科目 | POST | `/` | ADMIN | 创建新科目 | Body: `SubjectDTO` |
| 更新科目 | POST | `/{id}` | ADMIN | 更新科目信息 | Path: `id`, Body: `SubjectDTO` |
| 删除科目 | POST | `/{id}/delete` | ADMIN | 删除指定科目 | Path: `id` |
