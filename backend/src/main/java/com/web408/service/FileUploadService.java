package com.web408.service;

import com.web408.pojo.vo.ImageResourceVO;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * 文件上传服务接口
 * 遵循SOLID原则：单一职责，只处理文件上传相关业务
 */
public interface FileUploadService {
    
    /**
     * 上传图片
     * 
     * @param file 图片文件
     * @return 图片访问URL
     */
    String uploadImage(MultipartFile file);
    
    /**
     * 查询已上传图片列表
     * 
     * @param onlyUnreferenced 是否只查询未引用的图片
     * @return 图片资源列表
     */
    List<ImageResourceVO> listImages(Boolean onlyUnreferenced);
    
    /**
     * 删除未引用的图片
     * 
     * @return 删除的图片数量
     */
    int cleanupUnreferencedImages();
    
    /**
     * 删除指定图片
     * 
     * @param filename 文件名
     */
    void deleteImage(String filename);
}
