package com.web408.pojo.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * 章节请求DTO（创建和更新复用）
 * 用途：接收前端的章节创建/更新请求
 * 遵循KISS原则：简单的请求对象设计
 * 
 * Source: springdoc-openapi 官方文档
 */
@Schema(name = "章节信息", description = "章节信息（创建/更新）")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChapterDTO {
    /**
     * 所属科目ID（必填）
     */
    @Schema(description = "所属科目ID", example = "1", required = true)
    @NotNull(message = "科目ID不能为空")
    private Long subjectId;

    /**
     * 父章节ID（可选，NULL表示顶级章节）
     */
    @Schema(description = "父章节ID，为空表示顶级章节", example = "null", required = false)
    private Long parentId;

    /**
     * 章节名称（必填）
     */
    @Schema(description = "章节名称", example = "第一章 数据结构", required = true)
    @NotBlank(message = "章节名称不能为空")
    private String name;

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

