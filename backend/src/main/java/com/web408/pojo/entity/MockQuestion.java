package com.web408.pojo.entity;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 模拟题实体类
 * 对应数据库表: mock_question
 * 与真题独立，用于存储模拟题目
 */
@Data
public class MockQuestion {
    /**
     * 主键ID
     */
    private Long id;

    /**
     * 来源机构名称
     */
    private String source;

    /**
     * 题号
     */
    private Integer questionNumber;

    /**
     * 题型：CHOICE=选择题，ESSAY=主观题
     */
    private String questionType;

    /**
     * 题目标题（包含详细信息）
     */
    private String title;

    /**
     * Markdown格式题目内容
     * 选择题：题干
     * 主观题：完整题目
     */
    private String content;

    /**
     * 选择题选项（JSON格式字符串）
     * 示例：{"A":"选项A","B":"选项B","C":"选项C","D":"选项D"}
     * 主观题为NULL
     */
    private String options;

    /**
     * 答案
     * 选择题：正确选项（如"A"或"AB"多选）
     * 主观题：Markdown格式答案解析
     */
    private String answer;

    /**
     * 分类（支持多个分类）
     */
    private List<String> category;

    /**
     * 科目ID
     */
    private Long subjectId;

    /**
     * 难度: EASY/MEDIUM/HARD
     */
    private String difficulty;

    /**
     * 作者ID（外键关联user.id）
     */
    private Long authorId;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;
}
