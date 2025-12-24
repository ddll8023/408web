# Controller层规范文档

## 设计原则

所有Controller设计严格遵循以下核心原则：
- **KISS (Keep It Simple, Stupid)**：保持简单，Controller只负责接收请求、调用Service、返回响应
- **YAGNI (You Aren't Gonna Need It)**：不预设计未来可能需要的功能，只实现当前需求
- **SOLID**：单一职责原则，每个Controller只负责一个业务模块的接口

## 核心约束（不可违反）

### 1. 接口层职责边界
**Controller层严禁包含任何业务逻辑代码**，包括但不限于：
- ❌ 数据格式转换和处理逻辑
- ❌ 文件内容生成和格式化逻辑
- ❌ 复杂的条件判断和业务规则
- ❌ 数据计算和统计逻辑
- ❌ 字符串拼接和模板处理
- ❌ 文件操作和I/O处理

**Controller层只能包含**：
- ✅ 接收HTTP请求参数
- ✅ 调用Service层方法
- ✅ 返回统一格式的HTTP响应
- ✅ 基础的参数校验（通过注解）
- ✅ 权限控制（通过注解）

### 2. 异常处理策略
**优先使用全局异常处理器**，Controller中应避免try-catch：
```java
// ✅ 推荐：依赖全局异常处理
@GetMapping("/{id}")
public ResponseEntity<ApiResult<ExamVO>> getExamById(@PathVariable Long id) {
    ExamVO exam = examService.getExamById(id);
    return ResponseEntity.ok(ApiResult.success(exam, "查询成功"));
}

// ❌ 避免：冗余的异常处理
@GetMapping("/{id}")
public ResponseEntity<ApiResult<ExamVO>> getExamById(@PathVariable Long id) {
    try {
        ExamVO exam = examService.getExamById(id);
        return ResponseEntity.ok(ApiResult.success(exam, "查询成功"));
    } catch (Exception e) {
        return ResponseEntity.status(500).body(ApiResult.error(500, "查询失败：" + e.getMessage()));
    }
}
```

### 3. 用户认证处理
**禁止在每个方法中重复编写用户认证逻辑**，应使用以下方式之一：
- 创建BaseController提供通用方法
- 使用工具类封装用户获取逻辑
- 在Service层处理用户相关逻辑

## 基础结构规范

### 1. 导入规范（必须）

为避免代码中出现冗长的完全限定类名（如 `com.web408.pojo.vo.ApiResult`），所有Controller必须在文件开头正确导入所需的类：

```java
package com.web408.controller;

// 导入DTO、VO、Entity等
import com.web408.pojo.dto.ChapterDTO;
import com.web408.pojo.vo.ApiResult;
import com.web408.pojo.vo.ChapterVO;
import com.web408.service.ChapterService;

// 导入Swagger注解
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;

// 导入Spring注解
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

// 其他必要的导入
import java.util.List;
```

**注意**：
- 禁止在代码中使用完全限定类名（如 `com.web408.pojo.vo.ApiResult.success(...)`）
- 必须在文件开头正确导入所有使用的类
- 如果存在类名冲突（如 `io.swagger.v3.oas.annotations.responses.ApiResponse` 和 `com.web408.pojo.vo.ApiResult`），使用完全限定名导入其中一个，另一个使用简短名

### 2. 类级别注解（必须）

所有Controller类必须使用以下注解：

```java
@RestController
@RequestMapping("/api/{模块名}")
@Tag(name = "模块名称", description = "模块功能描述")
```

**示例**：
```java
@Tag(name = "章节管理", description = "提供章节查询和管理功能")
@RestController
@RequestMapping("/api/chapter")
public class ChapterController {
    // ...
}
```

### 3. 依赖注入规范

- 使用 `@Autowired` 注入Service层依赖
- 禁止在Controller中直接注入Mapper（除非特殊需求，如获取当前用户信息）
- 禁止在Controller中编写业务逻辑，所有业务逻辑应在Service层

**示例**：
```java
@Autowired
private ChapterService chapterService;

// 特殊需求：获取当前用户信息
@Autowired
private UserMapper userMapper;
```

### 4. HTTP方法使用规范

#### 标准RESTful方法（推荐）

- **GET**：查询操作（查询列表、查询详情、统计等）
- **POST**：创建操作
- **PUT**：更新操作（完整更新）
- **DELETE**：删除操作

#### 兼容性方法（允许）

考虑到前端兼容性和项目历史，以下方式也允许使用：
- **POST /{id}**：更新操作（部分Controller使用）
- **POST /{id}/delete**：删除操作（部分Controller使用）

**统一规范**：
- **新建Controller**：必须使用标准RESTful方法（GET/POST/PUT/DELETE）
- **现有Controller**：保持现有风格，逐步迁移

### 5. Swagger注解规范

#### 方法级别注解（必须）

所有接口方法必须使用以下Swagger注解：

```java
@Operation(summary = "接口简要说明", description = "接口详细描述")
@ApiResponse(responseCode = "200", description = "成功")
// 或使用 @ApiResponses 定义多个响应
@ApiResponses(value = {
    @ApiResponse(responseCode = "200", description = "成功"),
    @ApiResponse(responseCode = "400", description = "参数错误"),
    @ApiResponse(responseCode = "404", description = "资源不存在"),
    @ApiResponse(responseCode = "500", description = "服务器错误")
})
```

#### 参数注解（必须）

所有参数必须使用 `@Parameter` 注解：

```java
@Parameter(description = "参数说明", required = true, example = "示例值")
@PathVariable Long id

@Parameter(description = "参数说明", required = false)
@RequestParam(required = false) String name

@Parameter(description = "请求体说明", required = true)
@Valid @RequestBody DTO request
```

#### 权限注解（需要认证的接口）

需要JWT认证的接口必须添加：
```java
@SecurityRequirement(name = "JWT")
```

需要管理员权限的接口必须添加：
```java
@PreAuthorize("hasRole('ADMIN')")
```

**完整示例**：
```java
@Operation(summary = "创建章节", description = "创建新章节，仅管理员可访问")
@ApiResponse(responseCode = "200", description = "创建成功")
@SecurityRequirement(name = "JWT")
@PostMapping
@PreAuthorize("hasRole('ADMIN')")
public ResponseEntity<ApiResult<ChapterVO>> createChapter(
        @Parameter(description = "章节信息", required = true)
        @Valid @RequestBody ChapterDTO request) {
    // ...
}
```

### 6. 响应格式规范

#### 统一响应类型

所有接口必须返回 `ResponseEntity<ApiResult<T>>` 类型：

```java
// 成功响应
return ResponseEntity.ok(ApiResult.success(data, "操作成功"));

// 失败响应
return ResponseEntity.status(状态码).body(ApiResult.error(状态码, "错误信息"));
```

#### HTTP状态码使用规范

- **200 OK**：操作成功
- **400 Bad Request**：参数错误、业务逻辑错误（如用户名已存在）
- **401 Unauthorized**：未登录或认证失败
- **403 Forbidden**：无权限访问（通常由Spring Security自动处理）
- **404 Not Found**：资源不存在
- **500 Internal Server Error**：服务器内部错误

**注意**：`ApiResult` 中的 `code` 字段是业务状态码，与HTTP状态码保持一致。

### 7. 异常处理规范

#### 全局异常处理器

项目已配置 `GlobalExceptionHandler`，统一处理以下异常：
- `MethodArgumentNotValidException`：参数验证异常（自动返回400）
- `RuntimeException`：运行时异常（自动返回500）
- `Exception`：所有未捕获异常（自动返回500）

#### Controller异常处理策略

**推荐方式（依赖全局异常处理）**：
```java
@GetMapping("/{id}")
public ResponseEntity<ApiResult<ChapterVO>> getChapterById(
        @PathVariable Long id) {
    // 直接调用Service，异常由全局异常处理器处理
    ChapterVO chapter = chapterService.getChapterById(id);
    return ResponseEntity.ok(ApiResult.success(chapter, "查询成功"));
}
```

**兼容方式（需要特殊处理时）**：
```java
@PostMapping
public ResponseEntity<ApiResult<ChapterVO>> createChapter(
        @Valid @RequestBody ChapterDTO request) {
    try {
        ChapterVO chapter = chapterService.createChapter(request);
        return ResponseEntity.ok(ApiResult.success(chapter, "创建成功"));
    } catch (RuntimeException e) {
        // 需要特殊处理的业务异常
        return ResponseEntity.badRequest().body(ApiResult.error(400, e.getMessage()));
    } catch (Exception e) {
        // 需要特殊处理的系统异常
        return ResponseEntity.status(500).body(ApiResult.error(500, "创建失败：" + e.getMessage()));
    }
}
```

**统一规范**：
- **新建Controller**：优先使用全局异常处理，减少try-catch
- **现有Controller**：保持现有风格，逐步迁移
- **特殊业务场景**：需要特殊错误处理时，可以使用try-catch

### 8. 参数验证规范

#### DTO参数接收规范（核心）

**强制要求**：所有接口接收的请求体参数必须使用DTO类封装，禁止直接使用Entity或Map接收参数。

**标准写法**：
```java
@PostMapping
public ResponseEntity<ApiResult<ChapterVO>> createChapter(
        @Parameter(description = "章节信息", required = true)
        @Valid @RequestBody ChapterDTO request) {
    // ...
}
```

**参数注解组合说明**：
- `@Parameter`：Swagger文档注解，描述参数用途
- `@Valid`：触发DTO内部的Jakarta Bean Validation校验
- `@RequestBody`：标识从请求体中解析JSON数据

**DTO设计要求**（参考 `DTO-规范.md`）：
1. **命名规范**：`PascalCase + DTO`，如 `RegisterDTO`、`LoginDTO`
2. **场景派生**：创建用 `XxxCreateDTO`，更新用 `XxxUpdateDTO`；字段一致时可复用 `XxxDTO`
3. **必须使用Lombok**：`@Data` 必选，视需要添加 `@NoArgsConstructor`、`@AllArgsConstructor`
4. **校验注解**：
   - 非字符串必填：`@NotNull(message = "中文提示")`
   - 字符串必填：`@NotBlank(message = "中文提示")`
   - 长度限制：`@Size(min = X, max = Y, message = "中文提示")`
5. **OpenAPI注解**：类和字段都需要 `@Schema` 注解

**DTO示例**：
```java
@Schema(name = "用户注册请求", description = "用户注册请求")
@Data
public class RegisterDTO {
    @Schema(description = "用户名", example = "testuser", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 50, message = "用户名长度必须在3-50字符之间")
    private String username;

    @Schema(description = "密码", example = "123456", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 20, message = "密码长度必须在6-20字符之间")
    private String password;

    @Schema(description = "邮箱地址", example = "test@example.com", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
    @Email(message = "邮箱格式不正确")
    private String email;
}
```

**禁止的写法**：
```java
// ❌ 禁止：直接使用Entity接收参数
@PostMapping
public ResponseEntity<ApiResult<Void>> create(@RequestBody User user) { ... }

// ❌ 禁止：使用Map接收参数
@PostMapping
public ResponseEntity<ApiResult<Void>> create(@RequestBody Map<String, Object> params) { ... }

// ❌ 禁止：缺少@Valid注解
@PostMapping
public ResponseEntity<ApiResult<Void>> create(@RequestBody RegisterDTO request) { ... }
```

#### 路径参数和查询参数

- 路径参数：使用 `@PathVariable`，必须标注 `required = true`
- 查询参数：使用 `@RequestParam`，可选参数必须标注 `required = false` 并提供默认值

```java
@GetMapping("/{id}")
public ResponseEntity<ApiResult<ChapterVO>> getChapterById(
        @Parameter(description = "章节ID", required = true)
        @PathVariable Long id) {
    // ...
}

@GetMapping
public ResponseEntity<ApiResult<PageVO<ChapterVO>>> getChapterList(
        @Parameter(description = "页码", example = "1")
        @RequestParam(defaultValue = "1") int page,
        @Parameter(description = "每页大小", example = "10")
        @RequestParam(defaultValue = "10") int size,
        @Parameter(description = "科目ID筛选", required = false)
        @RequestParam(required = false) Long subjectId) {
    // ...
}
```

### 9. 权限控制规范

#### 权限级别

1. **公开接口**：无特殊注解，所有用户可访问
2. **需要认证**：添加 `@SecurityRequirement(name = "JWT")`
3. **需要管理员**：添加 `@SecurityRequirement(name = "JWT")` 和 `@PreAuthorize("hasRole('ADMIN')")`

#### 获取当前用户信息

**禁止在Controller中重复编写用户认证逻辑**。推荐以下方式：

**方式一：BaseController（推荐）**
```java
// 创建BaseController提供通用方法
public abstract class BaseController {
    @Autowired
    protected UserMapper userMapper;
    
    protected User getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String username = authentication.getName();
        User user = userMapper.findByUsername(username);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        return user;
    }
}

// 继承BaseController
@RestController
public class ExamController extends BaseController {
    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<ExamVO>> createExam(@Valid @RequestBody ExamDTO request) {
        // ✅ 简洁的用户获取
        User currentUser = getCurrentUser();
        ExamVO exam = examService.createExam(request, currentUser.getId());
        return ResponseEntity.ok(ApiResult.success(exam, "创建成功"));
    }
}
```

**方式二：Service层处理（推荐）**
```java
@PostMapping
@PreAuthorize("hasRole('ADMIN')")
public ResponseEntity<ApiResult<ExamVO>> createExam(@Valid @RequestBody ExamDTO request) {
    // ✅ 将用户认证逻辑委托给Service层
    ExamVO exam = examService.createExamWithCurrentUser(request);
    return ResponseEntity.ok(ApiResult.success(exam, "创建成功"));
}
```

**方式三：工具类（可选）**
```java
// 创建SecurityUtils工具类
public class SecurityUtils {
    public static User getCurrentUser(UserMapper userMapper) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String username = authentication.getName();
        User user = userMapper.findByUsername(username);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        return user;
    }
}

// 在Controller中使用
@PostMapping
@PreAuthorize("hasRole('ADMIN')")
public ResponseEntity<ApiResult<ExamVO>> createExam(@Valid @RequestBody ExamDTO request) {
    User currentUser = SecurityUtils.getCurrentUser(userMapper);
    ExamVO exam = examService.createExam(request, currentUser.getId());
    return ResponseEntity.ok(ApiResult.success(exam, "创建成功"));
}
```

**禁止的写法**：
```java
// ❌ 错误：在每个方法中重复编写认证逻辑
@PostMapping
public ResponseEntity<ApiResult<ExamVO>> createExam(@Valid @RequestBody ExamDTO request) {
    Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
    String username = authentication.getName();
    User user = userMapper.findByUsername(username);
    if (user == null) {
        return ResponseEntity.status(401).body(ApiResult.error(401, "用户不存在"));
    }
    // ...
}
```

### 10. 注释规范

#### 类级别注释（必须）

```java
/**
 * 章节控制器
 * 用途：提供章节管理的RESTful API接口
 * 遵循KISS原则：简单清晰的接口设计
 * 
 * 接口说明：
 * - GET /api/chapter/subject/{subjectId}：查询科目的章节树（仅启用）
 * - GET /api/chapter/subject/{subjectId}/all：查询科目的章节树（包含禁用，ADMIN专用）
 * - GET /api/chapter/{id}：根据ID查询章节
 * - POST /api/chapter：创建章节（ADMIN专用）
 * - POST /api/chapter/{id}：更新章节（ADMIN专用）
 * - POST /api/chapter/{id}/delete：删除章节（ADMIN专用）
 * 
 * Source: springdoc-openapi 官方文档
 */
```

#### 方法级别注释（必须）

```java
/**
 * 查询科目的启用章节树
 * 权限：公开
 */
@Operation(summary = "查询启用章节树", description = "根据科目ID查询该科目下所有启用的章节（树形结构）")
@ApiResponse(responseCode = "200", description = "查询成功")
@GetMapping("/subject/{subjectId}")
public ResponseEntity<ApiResponse<List<ChapterVO>>> getEnabledChapterTree(
        @Parameter(description = "科目ID", required = true)
        @PathVariable Long subjectId) {
    // ...
}
```

**注释要求**：
- 说明方法功能
- 标注权限要求（公开/需要认证/需要管理员）
- 复杂业务逻辑需要额外说明

### 11. 文件导出接口规范

#### 文件导出响应格式

**重要**：文件导出接口的所有业务逻辑（文件生成、格式处理、内容构建等）必须在Service层完成，Controller层只负责接收参数和返回文件流。

文件导出接口返回 `ResponseEntity<byte[]>`，不使用 `ApiResult`：

```java
@GetMapping("/export")
public ResponseEntity<byte[]> exportBySubject(
        @Parameter(description = "科目ID", required = true)
        @RequestParam Long subjectId,
        @Parameter(description = "导出格式", example = "markdown", required = true)
        @RequestParam String format) {
    // ✅ 正确：所有逻辑委托给Service层
    ExportResult exportResult = examService.exportBySubject(subjectId, format);
    
    HttpHeaders headers = new HttpHeaders();
    headers.setContentType(MediaType.parseMediaType(exportResult.getContentType()));
    headers.setContentDispositionFormData("attachment", 
            URLEncoder.encode(exportResult.getFilename(), StandardCharsets.UTF_8));
    headers.setContentLength(exportResult.getFileBytes().length);
    
    return ResponseEntity.ok()
            .headers(headers)
            .body(exportResult.getFileBytes());
}
```

**禁止的写法**：
```java
// ❌ 错误：在Controller中处理文件格式和内容生成
@GetMapping("/export")
public ResponseEntity<byte[]> exportBySubject(...) {
    try {
        List<ExamQuestion> exams = examService.exportBySubject(subjectId);
        
        // ❌ 这些逻辑应该在Service层
        if ("markdown".equalsIgnoreCase(format)) {
            StringBuilder sb = new StringBuilder();
            sb.append("# 真题导出\n\n");
            for (ExamQuestion exam : exams) {
                sb.append("## ").append(exam.getYear()).append("年 第")
                  .append(exam.getQuestionNumber()).append("题\n\n");
                // ... 更多格式处理逻辑
            }
            // ...
        }
        // ...
    } catch (Exception e) {
        // ❌ 应该使用全局异常处理
    }
}
```

**Service层应提供的ExportResult类**：
```java
public class ExportResult {
    private byte[] fileBytes;
    private String filename;
    private String contentType;
    // getters and setters
}
```

## 命名规范

### 1. 类名
- 以 `Controller` 结尾，如 `ChapterController`、`ExamController`
- 使用业务模块名称，如 `Chapter`、`Exam`、`Subject`

### 2. 方法名
- 查询方法：`get`、`find`、`list`、`query` 开头
- 创建方法：`create` 开头
- 更新方法：`update` 开头
- 删除方法：`delete` 开头
- 统计方法：`get` + `Stats`、`count` 开头

### 3. 路径命名
- 使用小写字母和连字符，如 `/api/chapter/subject/{subjectId}`
- 资源路径使用复数或单数保持一致，如 `/api/chapter`、`/api/exam`
- 子资源路径清晰表达层级关系，如 `/api/chapter/{id}/children`

## 完整示例模板

```java
package com.web408.controller;

// 导入DTO、VO、Entity等
import com.web408.pojo.dto.ChapterDTO;
import com.web408.pojo.vo.ApiResult;
import com.web408.pojo.vo.ChapterVO;
import com.web408.service.ChapterService;

// 导入Swagger注解
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;

// 导入Spring注解
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

// 其他必要的导入
import java.util.List;

/**
 * 章节控制器
 * 用途：提供章节管理的RESTful API接口
 * 遵循KISS原则：简单清晰的接口设计，无业务逻辑
 * 
 * 职责边界：
 * - ✅ 接收HTTP请求参数
 * - ✅ 调用Service层方法
 * - ✅ 返回统一格式响应
 * - ❌ 禁止包含任何业务逻辑
 * 
 * 接口说明：
 * - GET /api/chapter/subject/{subjectId}：查询科目的章节树（仅启用）
 * - GET /api/chapter/{id}：根据ID查询章节
 * - POST /api/chapter：创建章节（ADMIN专用）
 * - PUT /api/chapter/{id}：更新章节（ADMIN专用）
 * - DELETE /api/chapter/{id}：删除章节（ADMIN专用）
 * 
 * Source: springdoc-openapi 官方文档
 */
@Tag(name = "章节管理", description = "提供章节查询和管理功能")
@RestController
@RequestMapping("/api/chapter")
public class ChapterController {

    @Autowired
    private ChapterService chapterService;

    /**
     * 查询科目的启用章节树
     * 权限：公开
     */
    @Operation(summary = "查询启用章节树", description = "根据科目ID查询该科目下所有启用的章节（树形结构）")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/subject/{subjectId}")
    public ResponseEntity<ApiResult<List<ChapterVO>>> getEnabledChapterTree(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long subjectId) {
        List<ChapterVO> chapters = chapterService.getEnabledChapterTree(subjectId);
        return ResponseEntity.ok(ApiResult.success(chapters, "查询成功"));
    }

    /**
     * 根据ID查询章节
     * 权限：公开
     */
    @Operation(summary = "查询章节详情", description = "根据章节ID查询章节详细信息")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/{id}")
    public ResponseEntity<ApiResult<ChapterVO>> getChapterById(
            @Parameter(description = "章节ID", required = true)
            @PathVariable Long id) {
        ChapterVO chapter = chapterService.getChapterById(id);
        return ResponseEntity.ok(ApiResult.success(chapter, "查询成功"));
    }

    /**
     * 创建章节
     * 权限：ADMIN
     */
    @Operation(summary = "创建章节", description = "创建新章节，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "创建成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<ChapterVO>> createChapter(
            @Parameter(description = "章节信息", required = true)
            @Valid @RequestBody ChapterDTO request) {
        ChapterVO chapter = chapterService.createChapter(request);
        return ResponseEntity.ok(ApiResult.success(chapter, "创建成功"));
    }

    /**
     * 更新章节
     * 权限：ADMIN
     */
    @Operation(summary = "更新章节", description = "更新指定章节的信息，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "更新成功")
    @SecurityRequirement(name = "JWT")
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<ChapterVO>> updateChapter(
            @Parameter(description = "章节ID", required = true)
            @PathVariable Long id,
            @Parameter(description = "章节信息", required = true)
            @Valid @RequestBody ChapterDTO request) {
        ChapterVO chapter = chapterService.updateChapter(id, request);
        return ResponseEntity.ok(ApiResult.success(chapter, "更新成功"));
    }

    /**
     * 删除章节
     * 权限：ADMIN
     */
    @Operation(summary = "删除章节", description = "删除指定章节，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "删除成功")
    @SecurityRequirement(name = "JWT")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<Void>> deleteChapter(
            @Parameter(description = "章节ID", required = true)
            @PathVariable Long id) {
        chapterService.deleteChapter(id);
        return ResponseEntity.ok(ApiResult.success(null, "删除成功"));
    }
}
```

## 检查清单

创建或修改Controller时，请确保：

### 核心约束检查（必须）
- [ ] **Controller中无任何业务逻辑代码**（数据处理、格式转换、文件生成等）
- [ ] **优先使用全局异常处理，避免冗余try-catch**
- [ ] **用户认证逻辑不重复，使用BaseController或工具类**
- [ ] **文件导出等复杂逻辑完全委托给Service层**

### 基础规范检查
- [ ] 文件开头正确导入所有使用的类，避免使用完全限定类名
- [ ] 使用了 `@RestController`、`@RequestMapping`、`@Tag` 注解
- [ ] 所有接口方法都使用了 `@Operation` 和 `@ApiResponse` 注解
- [ ] 所有参数都使用了 `@Parameter` 注解
- [ ] 需要认证的接口添加了 `@SecurityRequirement(name = "JWT")`
- [ ] 需要管理员权限的接口添加了 `@PreAuthorize("hasRole('ADMIN')")`
- [ ] 所有接口返回 `ResponseEntity<ApiResult<T>>` 类型（文件导出除外）

### DTO和参数检查
- [ ] **请求体参数使用DTO封装，禁止直接使用Entity或Map**
- [ ] **DTO参数必须同时使用 `@Valid @RequestBody` 注解组合**
- [ ] **DTO类遵循 `DTO-规范.md` 的设计要求**

### 代码质量检查
- [ ] 类级别和方法级别都有完整的注释
- [ ] 方法名符合命名规范
- [ ] 路径命名清晰且符合RESTful风格
- [ ] HTTP方法使用统一（GET查询、POST创建/更新/删除）
- [ ] 代码简洁，每个方法只有3-5行核心逻辑

## 重构指导原则

基于KISS、YAGNI、SOLID原则，现有Controller如需重构，应遵循以下优先级：

### 1. 立即修复的问题（高优先级）
- **移除业务逻辑**：将所有数据处理、格式转换、文件生成等逻辑移至Service层
- **简化异常处理**：移除冗余try-catch，依赖全局异常处理器
- **消除代码重复**：提取用户认证等公共逻辑

### 2. 逐步优化的问题（中优先级）
- **统一HTTP方法**：新接口使用标准RESTful方法，现有接口保持兼容
- **完善注解**：补充缺失的Swagger注解和参数校验
- **优化命名**：方法名和路径名符合规范

### 3. 长期改进的问题（低优先级）
- **DTO规范化**：逐步将Entity参数替换为DTO
- **响应格式统一**：确保所有接口返回统一格式

## 注意事项

1. **业务逻辑分离**：Controller层绝对禁止包含业务逻辑，所有逻辑必须在Service层
2. **数据转换职责**：DTO到Entity的转换应在Service层完成，Controller层只负责接收DTO
3. **权限控制方式**：使用Spring Security注解进行权限控制，不在Controller中手动判断
4. **异常处理策略**：优先使用全局异常处理器，避免在Controller中编写try-catch
5. **代码复用原则**：提取公共逻辑到BaseController或工具类，避免重复代码
6. **性能优化考虑**：分页查询必须使用分页参数，避免一次性查询大量数据
7. **DTO使用规范**：所有请求体参数必须使用DTO封装，参考 `@Valid @RequestBody RegisterDTO request` 写法
8. **职责清晰分离**：入参使用DTO，出参使用VO，保持职责清晰

## 常见反模式及解决方案

### ❌ 反模式：Controller中包含复杂逻辑
```java
// 错误示例：在Controller中处理文件导出逻辑
@GetMapping("/export")
public ResponseEntity<byte[]> export(...) {
    List<ExamQuestion> exams = examService.getExams(...);
    StringBuilder sb = new StringBuilder();
    sb.append("# 真题导出\n\n");
    for (ExamQuestion exam : exams) {
        sb.append("## ").append(exam.getYear())...
    }
    // 大量格式处理逻辑...
}
```

### ✅ 正确做法：委托给Service层
```java
// 正确示例：Controller只负责调用Service
@GetMapping("/export")
public ResponseEntity<byte[]> export(...) {
    ExportResult result = examService.exportExams(subjectId, format);
    return ResponseEntity.ok()
            .headers(result.getHeaders())
            .body(result.getFileBytes());
}
```

### ❌ 反模式：重复的异常处理
```java
// 错误示例：每个方法都有相同的try-catch
@GetMapping("/{id}")
public ResponseEntity<ApiResult<ExamVO>> getExam(@PathVariable Long id) {
    try {
        ExamVO exam = examService.getExam(id);
        return ResponseEntity.ok(ApiResult.success(exam));
    } catch (Exception e) {
        return ResponseEntity.status(500).body(ApiResult.error(500, e.getMessage()));
    }
}
```

### ✅ 正确做法：依赖全局异常处理
```java
// 正确示例：简洁的Controller方法
@GetMapping("/{id}")
public ResponseEntity<ApiResult<ExamVO>> getExam(@PathVariable Long id) {
    ExamVO exam = examService.getExam(id);
    return ResponseEntity.ok(ApiResult.success(exam));
}
```

