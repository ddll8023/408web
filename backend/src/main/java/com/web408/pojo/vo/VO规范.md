# VO（View Object）规范文档

## 设计原则

所有VO设计严格遵循以下核心原则：
- **KISS (Keep It Simple, Stupid)**：保持简单，只包含必要字段
- **YAGNI (You Aren't Gonna Need It)**：只包含前端实际需要的字段，不预设计未来可能需要的字段
- **SOLID**：单一职责原则，每个VO只负责一个明确的数据传输场景

## 基础结构规范

### 1. Lombok注解（必须）
所有VO类必须使用以下Lombok注解：
```java
@Data
@NoArgsConstructor
@AllArgsConstructor
```

**例外情况**：
- `ApiResponse`：不使用Lombok，手动实现getter/setter和静态工厂方法
- `PageVO`：使用Lombok，但保留自定义构造方法

### 2. Swagger注解（必须）
所有VO类必须使用Swagger注解：
```java
@Schema(name = "VO名称", description = "VO用途说明")
```

所有字段必须使用：
```java
@Schema(description = "字段说明", example = "示例值")
```

### 3. 注释规范

#### 类注释（必须）
```java
/**
 * VO用途说明
 * 遵循YAGNI原则：只包含前端需要的字段
 */
```

#### 字段注释（必须）
每个字段必须有JavaDoc注释：
```java
/**
 * 字段说明
 */
@Schema(description = "字段说明", example = "示例值")
private Type fieldName;
```

## 命名规范

1. **类名**：以`VO`结尾，如`SubjectVO`、`ExamCategoryVO`
2. **字段名**：驼峰命名，与前端约定保持一致
3. **包路径**：`com.web408.pojo.vo`

## 字段设计原则

1. **只包含前端需要的字段**：不包含数据库内部字段（如createTime、updateTime等），除非前端明确需要
2. **关联数据扁平化**：如需要关联数据，使用扁平字段（如`subjectName`）而非嵌套对象，除非是树形结构
3. **统计字段**：统计类字段（如`questionCount`）应在VO中明确标注为统计字段
4. **树形结构**：支持树形结构的VO使用`List<SelfType> children`字段

## 特殊VO说明

### ApiResponse<T>
- **用途**：统一API响应封装
- **特点**：不使用Lombok，提供静态工厂方法（`success()`、`error()`）
- **位置**：`com.web408.pojo.vo.ApiResponse`

### PageVO<T>
- **用途**：统一分页响应格式
- **特点**：使用Lombok，但保留自定义构造方法（自动计算totalPages）
- **位置**：`com.web408.pojo.vo.PageVO`

## 示例模板

```java
package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * VO用途说明
 * 遵循YAGNI原则：只包含前端需要的字段
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "VO名称", description = "VO用途说明")
public class ExampleVO {
    /**
     * 字段说明
     */
    @Schema(description = "字段说明", example = "示例值")
    private Long id;

    /**
     * 字段说明
     */
    @Schema(description = "字段说明", example = "示例值")
    private String name;
}
```

## 检查清单

创建或修改VO时，请确保：
- [ ] 使用了`@Data`、`@NoArgsConstructor`、`@AllArgsConstructor`
- [ ] 类上使用了`@Schema`注解
- [ ] 所有字段都使用了`@Schema`注解
- [ ] 类注释说明了用途和设计原则
- [ ] 所有字段都有JavaDoc注释
- [ ] 只包含前端需要的字段
- [ ] 类名以`VO`结尾
- [ ] 字段命名符合驼峰规范

