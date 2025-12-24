package com.web408.pojo.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

/**
 * 模拟题创建DTO
 * 用于新增模拟题的数据传输
 */
@Data
@Schema(name = "模拟题创建请求", description = "模拟题创建请求体")
public class MockQuestionCreateDTO {

    @Schema(description = "来源机构名称", example = "王道", required = true)
    @NotBlank(message = "来源机构不能为空")
    private String source;

    @Schema(description = "题号", example = "1", required = false)
    private Integer questionNumber;

    @Schema(description = "题型：CHOICE=选择题，ESSAY=主观题", example = "CHOICE", required = true)
    @NotBlank(message = "题型不能为空")
    private String questionType;

    @Schema(description = "题目标题", example = "2024王道模拟卷一 第1题", required = false)
    private String title;

    @Schema(description = "Markdown格式题目内容", example = "以下关于栈的说法，正确的是...", required = true)
    @NotBlank(message = "题目内容不能为空")
    private String content;

    @Schema(description = "选择题选项（JSON格式）", example = "{\"A\":\"选项A\",\"B\":\"选项B\"}", required = false)
    private String options;

    @Schema(description = "答案", example = "A", required = true)
    @NotBlank(message = "答案不能为空")
    private String answer;

    @Schema(description = "分类列表", example = "[\"栈和队列\", \"数据结构\"]", required = false)
    private List<String> category;

    @Schema(description = "科目ID", example = "1", required = true)
    @NotNull(message = "科目ID不能为空")
    private Long subjectId;

    @Schema(description = "难度：EASY/MEDIUM/HARD", example = "MEDIUM", required = false)
    private String difficulty;
}
