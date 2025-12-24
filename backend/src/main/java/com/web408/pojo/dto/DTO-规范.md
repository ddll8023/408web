# DTO 规范（com.web408.pojo.dto）

- **适用范围**
  - DTO 仅承载接口入参/出参数据；不包含业务逻辑、持久化/JPA 注解、服务依赖。

- **包与命名**
  - 包：`com.web408.pojo.dto`
  - 类名：`PascalCase + DTO`；按场景派生 `CreateDTO`/`UpdateDTO`；创建与更新字段一致时复用 `XxxDTO`。

- **Lombok**
  - 必选：`@Data`
  - 视需要：`@NoArgsConstructor`、`@AllArgsConstructor`

- **校验（Jakarta Bean Validation）**
  - 必填（非字符串）：`@NotNull`；字符串：`@NotBlank`
  - 长度限制：`@Size(max = X)`
  - 校验消息：必须使用中文 `message`
  - 类型：优先包装类型 `Long/Integer/Boolean` 以表达可空性
  - 更新策略：全量更新可与创建复用；部分更新（PATCH）另建 `XxxUpdateDTO`

- **OpenAPI 注解（springdoc-openapi）**
  - 类：`@Schema(name = "中文名称", description = "用途/语义")`
  - 字段：所有字段一律标注 `@Schema(description = "含义", example = "示例", required = true/false)`
  - `name` 字段使用规范：
    - 用作 OpenAPI 展示名（推荐中文），不改变 JSON key。
    - 类上必须设置 `name`；字段上仅在与实际字段名不同或需提升可读性时设置。
  - `required` 与校验一致：`@NotNull/@NotBlank => required = true`

- **字段命名与语义**
  - 命名：`lowerCamelCase`
  - 标识/外键：`xxxId`（如 `subjectId`、`parentId`）
  - 序号：`orderNum`
  - 布尔：`enabled`（类型 `Boolean`）

- **类型与取值**
  - 可选值：短期使用 `String` 并在 `@Schema`/注释中列出（如 `questionType`、`difficulty`）
  - 仅在跨层复用或需强约束时抽取 `enum`（YAGNI）

- **结构化内容**
  - 简单结构允许 `String` 承载 JSON（如 `options`）；复杂场景再引入专用 DTO 或 `Map`

- **本地化与示例**
  - 注释与校验消息使用中文；示例值贴近业务

- **与现有类对齐**
  - ChapterDTO：`subjectId(Long, 必填)`, `parentId(Long, 可选)`, `name(String, 必填)`, `orderNum(Integer, 必填)`, `enabled(Boolean, 必填)`
  - ExamQuestionCreateDTO：`year(Integer, 必填)`, `questionNumber(Integer, 可选)`, `questionType(String, 必填)`, `title(String, 可选, <=200)`, `content(String, 必填)`, `options(String, 可选 JSON)`, `answer(String, 可选)`, `category(String, 必填, <=50)`, `difficulty(String, 可选)`
