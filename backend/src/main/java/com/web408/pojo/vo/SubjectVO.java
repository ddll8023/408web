package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 科目视图对象
 * 用途：返回给前端的科目数据
 * 遵循YAGNI原则：只包含前端需要的字段
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "SubjectVO", description = "科目视图对象")
public class SubjectVO {
    /**
     * 科目ID
     */
    @Schema(description = "科目ID", example = "1")
    private Long id;

    /**
     * 科目名称
     */
    @Schema(description = "科目名称", example = "数据结构")
    private String name;

    /**
     * 科目编码
     */
    @Schema(description = "科目编码", example = "data-structure")
    private String code;

    /**
     * 科目描述
     */
    @Schema(description = "科目描述", example = "数据结构相关题目")
    private String description;

    /**
     * 排序序号
     */
    @Schema(description = "排序序号", example = "1")
    private Integer orderNum;

    /**
     * 是否启用
     */
    @Schema(description = "是否启用", example = "true")
    private Boolean enabled;

    /**
     * 题目总数（统计）
     */
    @Schema(description = "题目总数（统计）", example = "100")
    private Integer questionCount;
}

