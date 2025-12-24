package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 真题年份统计视图对象
 * 用途：返回给前端的年份统计数据
 * 遵循YAGNI原则：只包含前端需要的字段
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "ExamYearStatVO", description = "真题年份统计视图对象")
public class ExamYearStatVO {
    /**
     * 年份
     */
    @Schema(description = "年份", example = "2023")
    private Integer year;

    /**
     * 题目数量（统计）
     */
    @Schema(description = "题目数量（统计）", example = "50")
    private Long count;
}
