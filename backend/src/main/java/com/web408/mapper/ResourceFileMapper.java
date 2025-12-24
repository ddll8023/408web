package com.web408.mapper;

import com.web408.pojo.entity.ResourceFile;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 资源文件Mapper接口
 */
@Mapper
public interface ResourceFileMapper {
    
    /**
     * 插入资源文件
     * 
     * @param resourceFile 资源文件对象
     * @return 影响行数
     */
    int insert(ResourceFile resourceFile);

    /**
     * 根据ID查询资源文件
     * 
     * @param id 资源文件ID
     * @return ResourceFile对象，不存在返回null
     */
    ResourceFile findById(@Param("id") Long id);

    /**
     * 查询所有资源文件
     * 
     * @return 资源文件列表
     */
    List<ResourceFile> findAll();

    /**
     * 根据上传者ID查询资源文件
     * 
     * @param uploaderId 上传者ID
     * @return 资源文件列表
     */
    List<ResourceFile> findByUploaderId(@Param("uploaderId") Long uploaderId);

    /**
     * 删除资源文件
     * 
     * @param id 资源文件ID
     * @return 影响行数
     */
    int deleteById(@Param("id") Long id);

    /**
     * 增加下载次数
     * 
     * @param id 资源文件ID
     * @return 影响行数
     */
    int incrementDownloadCount(@Param("id") Long id);
}

