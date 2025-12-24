package com.web408.pojo.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 分类标签实体类
 * 对应数据库表：exam_category
 * 用途：按科目管理题目分类标签
 * 遵循KISS原则：简单清晰的实体类设计
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ExamCategory {
    /**
     * 主键ID
     */
    private Long id;

    /**
     * 所属科目ID
     */
    private Long subjectId;

    /**
     * 父分类ID（NULL表示顶级分类）
     */
    private Long parentId;

    /**
     * 分类名称（如：栈和队列、进程管理等）
     */
    private String name;

    /**
     * 分类编码（如：stack-queue、process等）
     */
    private String code;

    /**
     * 分类描述（可选）
     */
    private String description;

    /**
     * 排序序号（升序）
     */
    private Integer orderNum;

    /**
     * 是否启用
     */
    private Boolean enabled;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;
}
