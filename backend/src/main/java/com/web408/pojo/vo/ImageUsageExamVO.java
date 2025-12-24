package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "ImageUsageExamVO", description = "图片引用的真题信息")
public class ImageUsageExamVO {

    @Schema(description = "真题ID", example = "1")
    private Long id;

    @Schema(description = "年份", example = "2023")
    private Integer year;

    @Schema(description = "题号", example = "3")
    private Integer questionNumber;

    @Schema(description = "标题", example = "操作系统-进程管理")
    private String title;
}
