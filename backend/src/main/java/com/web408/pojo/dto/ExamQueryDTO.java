package com.web408.pojo.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 真题分页查询请求DTO
 * 用于封装分页查询的多个参数
 */
@Schema(name = "真题查询请求", description = "真题分页查询请求参数")
@Data
public class ExamQueryDTO {
    
    @Schema(description = "页码", example = "1")
    private Integer page = 1;
    
    @Schema(description = "每页大小", example = "10")
    private Integer size = 10;
    
    @Schema(description = "年份筛选", example = "2023")
    private Integer year;
    
    @Schema(description = "分类筛选", example = "数据结构")
    private String category;
    
    @Schema(description = "科目ID", example = "1")
    private Long subjectId;
    
    @Schema(description = "是否筛选无分类的题目", example = "false")
    private Boolean noCategory;
    
    @Schema(description = "搜索关键词", example = "二叉树")
    private String keyword;
    
    @Schema(description = "排序字段", example = "year")
    private String sortField;
    
    @Schema(description = "排序方向，可选：asc、desc", example = "desc")
    private String sortOrder;
}
