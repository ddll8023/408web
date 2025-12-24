package com.web408.pojo.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 科目实体类
 * 对应数据库表：subject
 * 用途：管理408科目配置（数据结构、操作系统、计算机网络、计算机组成原理等）
 * 遵循KISS原则：简单清晰的实体类设计
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Subject {
    /**
     * 主键ID
     */
    private Long id;

    /**
     * 科目名称（如：数据结构、操作系统等）
     */
    private String name;

    /**
     * 科目编码（用于URL参数，如：data-structure）
     */
    private String code;

    /**
     * 科目描述（Markdown格式，可选）
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

