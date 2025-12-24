package com.web408.pojo.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;
import java.util.List;

/**
 * 真题创建请求DTO
 * 遵循SOLID原则：单一职责，仅用于接收创建请求参数
 */
@Schema(name = "真题创建请求", description = "真题创建请求")
@Data
public class ExamQuestionCreateDTO {
    
    /**
     * 年份（必填）
     */
    @Schema(description = "年份", example = "2023", required = true)
    @NotNull(message = "年份不能为空")
    private Integer year;
    
    @Schema(description = "科目ID", example = "1", required = false)
    private Long subjectId;
    
    /**
     * 题号（可选）
     */
    @Schema(description = "题号", example = "1", required = false)
    private Integer questionNumber;
    
    /**
     * 题型（必填）
     * 可选值：CHOICE（选择题）、ESSAY（主观题）
     */
    @Schema(description = "题型，可选：CHOICE、ESSAY", example = "CHOICE", required = true)
    @NotBlank(message = "题型不能为空")
    private String questionType;
    
    /**
     * 题目标题（可选，最大200字符）
     */
    @Schema(description = "标题", example = "数据结构 - 栈", required = false)
    @Size(max = 200, message = "标题长度不能超过200字符")
    private String title;
    
    /**
     * Markdown格式题目内容（必填）
     * 选择题：题干
     * 主观题：完整题目
     */
    @Schema(description = "题目内容（Markdown）", example = "给定一个栈，判断序列是否合法", required = true)
    @NotBlank(message = "题目内容不能为空")
    private String content;
    
    /**
     * 选择题选项（JSON格式字符串，选择题必填）
     * 示例：{"A":"选项A","B":"选项B","C":"选项C","D":"选项D"}
     */
    @Schema(description = "选择题选项（JSON字符串）", example = "{\"A\":\"选项A\",\"B\":\"选项B\",\"C\":\"选项C\",\"D\":\"选项D\"}", required = false)
    private String options;
    
    /**
     * 答案（可选）
     * 选择题：正确选项（如"A"或"AB"）
     * 主观题：Markdown格式答案解析
     */
    @Schema(description = "答案", example = "A", required = false)
    private String answer;
    
    /**
     * 分类（支持多个分类）
     * 可选值：数据结构、操作系统、计算机网络、计算机组成原理
     */
    @Schema(description = "分类（支持多个）", example = "[\"数据结构\", \"操作系统\"]", required = false)
    private List<String> category;
    
    /**
     * 难度（可选）
     * 可选值：EASY、MEDIUM、HARD
     */
    @Schema(description = "难度，可选：EASY、MEDIUM、HARD", example = "MEDIUM", required = false)
    private String difficulty;
}
