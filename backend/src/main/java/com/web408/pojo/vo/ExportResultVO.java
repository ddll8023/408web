package com.web408.pojo.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 文件导出结果VO
 * 用途：封装文件导出的结果数据，包含文件字节、文件名和内容类型
 * 遵循KISS原则：简单的数据传输对象
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ExportResultVO {
    
    /**
     * 文件字节内容
     */
    private byte[] fileBytes;
    
    /**
     * 文件名
     */
    private String filename;
    
    /**
     * 内容类型（MIME类型）
     */
    private String contentType;
}
