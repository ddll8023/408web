package com.web408.pojo.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 章节实体类
 * 对应数据库表：chapter
 * 用途：管理知识点章节结构（支持两级：父章节-子章节）
 * 遵循KISS原则：简单的树形结构设计
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Chapter {
    /**
     * 主键ID
     */
    private Long id;

    /**
     * 所属科目ID
     */
    private Long subjectId;

    /**
     * 父章节ID（NULL表示顶级章节）
     */
    private Long parentId;

    /**
     * 章节名称
     */
    private String name;

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

