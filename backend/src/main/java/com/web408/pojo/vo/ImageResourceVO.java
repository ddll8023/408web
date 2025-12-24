package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 图片资源视图对象
 * 用于向前端返回 uploads/images 下的图片信息
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "ImageResourceVO", description = "图片资源视图对象")
public class ImageResourceVO {
    /**
     * 文件名
     */
    @Schema(description = "文件名", example = "123456.png")
    private String filename;

    /**
     * 访问URL
     */
    @Schema(description = "访问URL", example = "/uploads/images/123456.png")
    private String url;

    /**
     * 文件大小（字节）
     */
    @Schema(description = "文件大小（字节）", example = "204800")
    private long size;

    /**
     * 最后修改时间（毫秒时间戳）
     */
    @Schema(description = "最后修改时间（毫秒时间戳）", example = "1719744000000")
    private long lastModified;

    @Schema(description = "是否被题目引用（真题、模拟题、课后习题）")
    private boolean referenced;

    @Schema(description = "引用该图片的题目列表（包括真题、模拟题、课后习题）")
    private List<ImageUsageExamVO> exams;
}
