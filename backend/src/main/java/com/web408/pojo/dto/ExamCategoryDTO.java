package com.web408.pojo.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * 分类标签请求DTO（创建和更新复用）
 * 用途：接收前端的分类创建/更新请求
 * 遵循KISS原则：简单的请求对象设计
 */
@Schema(name = "分类标签信息", description = "分类标签信息（创建/更新）")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ExamCategoryDTO {
    /**
     * 所属科目ID（必填）
     */
    @Schema(description = "所属科目ID", example = "1", required = true)
    @NotNull(message = "科目ID不能为空")
    private Long subjectId;

    /**
     * 父分类ID（可选，NULL表示顶级分类）
     */
    @Schema(description = "父分类ID（NULL表示顶级分类）", example = "1", required = false)
    private Long parentId;

    /**
     * 分类名称（必填）
     */
    @Schema(description = "分类名称", example = "栈和队列", required = true)
    @NotBlank(message = "分类名称不能为空")
    private String name;

    /**
     * 分类编码（必填）
     */
    @Schema(description = "分类编码", example = "stack-queue", required = true)
    @NotBlank(message = "分类编码不能为空")
    private String code;

    /**
     * 分类描述（可选）
     */
    @Schema(description = "分类描述", example = "包含栈、队列及其应用的相关题目", required = false)
    private String description;

    /**
     * 排序序号（必填）
     */
    @Schema(description = "排序序号", example = "1", required = true)
    @NotNull(message = "排序序号不能为空")
    private Integer orderNum;

    /**
     * 是否启用（必填）
     */
    @Schema(description = "是否启用", example = "true", required = true)
    @NotNull(message = "启用状态不能为空")
    private Boolean enabled;
}
