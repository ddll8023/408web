package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 真题分类统计视图对象
 * 用于管理端的分类统计和筛选功能
 * 遵循KISS原则：简单清晰的数据传输对象
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "ExamCategoryStatVO", description = "真题分类统计视图对象")
public class ExamCategoryStatVO {
    
    /**
     * 科目ID
     */
    @Schema(description = "科目ID", example = "1")
    private Long subjectId;
    
    /**
     * 科目名称
     */
    @Schema(description = "科目名称", example = "数据结构")
    private String subjectName;
    
    /**
     * 分类名称
     */
    @Schema(description = "分类名称", example = "栈和队列")
    private String category;
    
    /**
     * 题目数量
     */
    @Schema(description = "题目数量", example = "15")
    private Long count;

    @Schema(description = "选择题数量", example = "10")
    private Long choiceCount;

    @Schema(description = "主观题数量", example = "5")
    private Long subjectiveCount;
    
    /**
     * 题目列表（年份-题号格式，如 "2023-1", "2022-5"）
     */
    @Schema(description = "题目列表", example = "[\"2023-1\", \"2023-5\", \"2022-3\"]")
    private List<String> questions;
    
    /**
     * 题目字符串（SQL查询结果，用于转换为questions列表）
     * 该字段不对外暴露，仅用于内部数据转换
     */
    @Schema(hidden = true)
    private String questionsStr;
    
    /**
     * 设置questionsStr时自动解析为questions列表
     * 遵循KISS原则：setter中直接完成转换
     */
    public void setQuestionsStr(String questionsStr) {
        this.questionsStr = questionsStr;
        if (questionsStr != null && !questionsStr.isEmpty()) {
            this.questions = java.util.Arrays.asList(questionsStr.split(","));
        }
    }
}
