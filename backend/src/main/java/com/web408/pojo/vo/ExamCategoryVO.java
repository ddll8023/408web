package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 分类标签视图对象
 * 用途：返回给前端的分类数据
 * 遵循YAGNI原则：只包含前端需要的字段
 */
@Schema(name = "分类标签响应", description = "分类标签信息")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ExamCategoryVO {
    /**
     * 分类ID
     */
    @Schema(description = "分类ID", example = "1")
    private Long id;

    /**
     * 所属科目ID
     */
    @Schema(description = "所属科目ID", example = "1")
    private Long subjectId;

    /**
     * 所属科目名称（关联查询）
     */
    @Schema(description = "所属科目名称", example = "数据结构")
    private String subjectName;

    /**
     * 父分类ID
     */
    @Schema(description = "父分类ID", example = "1")
    private Long parentId;

    /**
     * 父分类名称（关联查询）
     */
    @Schema(description = "父分类名称", example = "线性表")
    private String parentName;

    /**
     * 分类名称
     */
    @Schema(description = "分类名称", example = "栈和队列")
    private String name;

    /**
     * 分类编码
     */
    @Schema(description = "分类编码", example = "stack-queue")
    private String code;

    /**
     * 分类描述
     */
    @Schema(description = "分类描述", example = "包含栈、队列及其应用的相关题目")
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
     * 引用题目数量（统计）
     */
    @Schema(description = "引用题目数量", example = "25")
    private Integer questionCount;

    /**
     * 子分类列表（树形结构）
     */
    @Schema(description = "子分类列表")
    private List<ExamCategoryVO> children;
}
