package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 分类统计视图对象
 * 用途：返回分类名称及其题目数量
 * 遵循KISS原则：只包含必要的字段
 */
@Schema(name = "分类统计响应", description = "分类名称及题目数量")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CategoryStatVO {
    
    /**
     * 分类名称
     */
    @Schema(description = "分类名称", example = "栈和队列")
    private String name;
    
    /**
     * 题目数量
     */
    @Schema(description = "题目数量", example = "25")
    private Integer questionCount;
}
