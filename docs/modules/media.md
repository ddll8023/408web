# 图片资源

模块标识：`media`。返回 [项目结构](../项目结构文档.md)。

## 职责与入口

图片上传、资源清单、引用状态扫描与未引用文件清理。`uploads/images/` 是**唯一**图片目录：题目 Markdown 插图、真题过程图片、管理端上传都落在这里。

入口（前缀 `/api/upload`，见 `backend-fastapi/src/web408/modules/media/router.py`，全部要求管理员）：

- `POST /api/upload/image`（上传）
- `POST /api/upload/images`（列表，可只列未引用）
- `POST /api/upload/images/cleanup`（清理未引用）
- `POST /api/upload/image/delete`（删除指定文件）
- 前端：`frontend/src/views/admin/ImageManage.vue`（管理页）；`components/basic/MarkdownEditor.vue` 通过 `api/upload.ts#uploadImage` 上传；`ExamProcessDialog.vue` 用 `getImageUrl` 取地址。

不负责：真题过程图片的关联与排序（[真题](exam.md)）；题目正文里的图片语义（[公共记录](shared.md#题目渲染与复制导出共享)）。

## 专属文件

| 文件 | 当前用途及纳入依据 |
| --- | --- |
| `backend-fastapi/src/web408/modules/media/router.py` | 四个 HTTP 用例；`get_upload_service` 从配置注入目录与大小上限 |
| `backend-fastapi/src/web408/modules/media/service.py` | `UploadService`：扩展名/Content-Type/文件头签名校验、暂存-提交式写入、列表、引用标记、删除与未引用清理 |
| `backend-fastapi/src/web408/modules/media/reference_reader.py` | `MediaReferenceReader`：通过 exam / mock / adaptation 的 Query Service 与 `ExamProcessImageReadService` 扫描文件名引用 |
| `backend-fastapi/src/web408/modules/media/schemas.py` | 列表/删除/清理请求、`ImageResourceResponse`、`ImageUsageResponse` |
| `backend-fastapi/src/web408/integrations/local_file_storage.py` | `LocalFileStorage`：暂存上传、提交、丢弃、路径安全校验、删除（被 media 与 exam 过程图片共用） |
| `frontend/src/api/upload.ts` | `uploadImage`、`getImageUrl`、`normalizeImageUrls`、`getImageList`、`deleteImage`、`deleteUnreferencedImages` |
| `frontend/src/types/image.ts` | 图片资源与引用类型 |
| `frontend/src/views/admin/ImageManage.vue` | 图片列表、预览、引用信息、删除与未引用清理 |

## 公共与跨模块引用

| 所属 | 文件与使用范围 | 本模块为何引用 |
| --- | --- | --- |
| `exam` 模块 | `ExamQueryService#list_image_reference_texts`、`ExamProcessImageReadService#list_for_media_reference` | 判定真题正文与过程图片的引用 |
| `mock` 模块 | `MockQueryService#list_image_reference_texts` | 判定模拟题引用 |
| `adaptation` 模块 | `AdaptationQueryService#list_image_reference_texts` | 判定改编题引用 |
| [公共记录](shared.md) | `frontend/src/styles/*`、基础组件、`utils/toast` | 管理页展示 |

被引用方向：`exam`（过程图片上传复用 `UploadService`）、`MarkdownEditor`（编辑时上传）、`utils/markdownSourceMapping.ts`（`normalizeImageUrls`）。

## 关键调用链

上传：

1. `MarkdownEditor.vue` 或 `ImageManage.vue` → `POST /api/upload/image`（`multipart/form-data`）。
2. `UploadService.upload_image`：校验扩展名与 `Content-Type` 匹配 → `LocalFileStorage.stage_upload` 分块写入临时文件并记录头部字节 → 文件头签名校验 → `commit_upload` 落盘。
3. 任一步失败都 `discard_upload` 清理临时文件；成功返回 `/uploads/images/<uuid>.<ext>`，由 `main.py` 的 `StaticFiles` 直接对外。

引用扫描与清理：

1. `ImageManage.vue` 打开 → `POST /api/upload/images`。
2. `UploadService.list_images` 列出目录文件 → `MediaReferenceReader.mark_references` 用**文件名子串**匹配三类题目文本（content/answer/options）与过程图片表，标记 `referenced` 并附使用位置。
3. 清理接口只删未被标记引用的文件，且要求 `confirm` 为真；扫描与删除之间可能发生题目保存，所以逐文件再 `_is_image_referenced` 复核。单个删除走 `safe_file_path` 校验，并在被引用时直接拒绝（`ConflictException`）。

## 状态与数据所有者

| 状态／资源 | 所有者 | 副本或消费者 | 生命周期／持久化 |
| --- | --- | --- | --- |
| 物理图片文件 | `uploads/images/`（`UPLOAD_DIR`） | 题目 Markdown、过程图片关联、管理页 | 磁盘持久；文件名随机化，无数据库记录 |
| 引用关系 | 无独立表，由文本扫描派生 | 管理页「引用状态」、清理判定 | 临时计算，不入库 |
| 上传大小上限 | `core/config.py#UploadConfig.max_file_size`（`MAX_FILE_SIZE`，默认 10 MB） | 上传校验 | 配置驱动 |

## 生命周期与约束

- 扩展名白名单 `jpg/jpeg/png/gif/webp`，且 `Content-Type` 必须与扩展名一致；再校验文件头签名，三者都过才落盘。
- 引用判定是**字符串包含**而非正则或 AST，文件名出现在任何题目文本或过程图片记录中都视为已引用；删除文件后不会自动修复题目里的失效链接。
- 删除与清理都要求显式 `confirm`，且删除前重新扫描，不接受前端传来的「未引用」结论。
- 过程图片删除只解除关联，物理文件由本模块的未引用清理处理。

## 当前覆盖边界

- 清理接口在并发上传/删除下的竞态、以及大目录扫描性能未静态确认。
- 仓库中 `backend-fastapi/uploads/images/` 当前有被 git 跟踪的图片文件，历史成因与影响需单独确认，本文不做清理建议。
