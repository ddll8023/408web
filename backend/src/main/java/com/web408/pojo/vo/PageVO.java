package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 分页响应视图对象
 * 用途：统一分页数据返回格式
 * 遵循KISS原则：结构简单清晰
 * 遵循YAGNI原则：只包含前端需要的字段
 * 
 * @param <T> 数据类型
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "PageVO", description = "分页响应视图对象")
public class PageVO<T> {
    /**
     * 数据列表
     */
    @Schema(description = "数据列表")
    private List<T> data;

    /**
     * 总记录数
     */
    @Schema(description = "总记录数", example = "100")
    private long total;

    /**
     * 当前页码（从1开始）
     */
    @Schema(description = "当前页码（从1开始）", example = "1")
    private int page;

    /**
     * 每页大小
     */
    @Schema(description = "每页大小", example = "10")
    private int size;

    /**
     * 总页数
     */
    @Schema(description = "总页数", example = "10")
    private int totalPages;

    /**
     * 构造方法（自动计算总页数）
     * 
     * @param data 数据列表
     * @param total 总记录数
     * @param page 当前页码
     * @param size 每页大小
     */
    public PageVO(List<T> data, long total, int page, int size) {
        this.data = data;
        this.total = total;
        this.page = page;
        this.size = size;
        this.totalPages = (int) Math.ceil((double) total / size);
    }
}

