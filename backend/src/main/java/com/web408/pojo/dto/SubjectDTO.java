package com.web408.pojo.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * 科目请求DTO（创建和更新复用）
 * 用途：接收前端的科目创建/更新请求
 * 遵循KISS原则：简单的请求对象设计
 * 
 * Source: springdoc-openapi 官方文档
 */
@Schema(name = "科目信息", description = "科目信息（创建/更新）")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SubjectDTO {
    /**
     * 科目名称（必填）
     */
    @Schema(description = "科目名称", example = "计算机组成原理", required = true)
    @NotBlank(message = "科目名称不能为空")
    private String name;

    /**
     * 科目编码（必填）
     */
    @Schema(description = "科目编码", example = "COA", required = true)
    @NotBlank(message = "科目编码不能为空")
    private String code;

    /**
     * 科目描述（可选）
     */
    @Schema(description = "科目描述", example = "计算机组成原理课程", required = false)
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

