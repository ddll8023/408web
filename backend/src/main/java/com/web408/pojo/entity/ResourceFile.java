package com.web408.pojo.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 资源文件实体类
 * 对应数据库表: resource_file
 */
@Data
public class ResourceFile {
    /**
     * 主键ID
     */
    private Long id;

    /**
     * 存储文件名（UUID生成）
     */
    private String filename;

    /**
     * 原始文件名
     */
    private String originalFilename;

    /**
     * 文件存储路径
     */
    private String filePath;

    /**
     * 文件大小（字节）
     */
    private Long fileSize;

    /**
     * 文件类型
     */
    private String fileType;

    /**
     * 资源描述
     */
    private String description;

    /**
     * 下载次数
     */
    private Integer downloadCount;

    /**
     * 上传者ID（外键关联user.id）
     */
    private Long uploaderId;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;
}

