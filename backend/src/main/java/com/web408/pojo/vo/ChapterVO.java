package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 章节视图对象
 * 用途：返回给前端的章节数据（支持树形结构）
 * 遵循YAGNI原则：只包含前端需要的字段
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "ChapterVO", description = "章节视图对象")
public class ChapterVO {
    /**
     * 章节ID
     */
    @Schema(description = "章节ID", example = "1")
    private Long id;

    /**
     * 所属科目ID
     */
    @Schema(description = "所属科目ID", example = "1")
    private Long subjectId;

    /**
     * 父章节ID
     */
    @Schema(description = "父章节ID", example = "1")
    private Long parentId;

    /**
     * 章节名称
     */
    @Schema(description = "章节名称", example = "第一章 绪论")
    private String name;

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
     * 子章节列表（用于前端树形展示）
     */
    @Schema(description = "子章节列表")
    private List<ChapterVO> children;
}

