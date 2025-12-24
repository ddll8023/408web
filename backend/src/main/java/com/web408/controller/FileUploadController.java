package com.web408.controller;

import com.web408.pojo.vo.ApiResult;
import com.web408.pojo.vo.ImageResourceVO;
import com.web408.service.FileUploadService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * 文件上传控制器
 * 用途：提供图片上传功能，用于Markdown编辑器
 * 遵循KISS原则：简单清晰的接口设计，无业务逻辑
 * 
 * 职责边界：
 * - ✅ 接收HTTP请求参数
 * - ✅ 调用Service层方法
 * - ✅ 返回统一格式响应
 * - ❌ 禁止包含任何业务逻辑
 * 
 * 接口说明：
 * - POST /api/upload/image：上传图片
 * - GET /api/upload/images：查询已上传图片列表（ADMIN专用）
 * - POST /api/upload/images/cleanup：删除所有未被真题引用的图片（ADMIN专用）
 * - POST /api/upload/image/delete：删除已上传图片（ADMIN专用）
 * 
 * Source: springdoc-openapi 官方文档
 */
@Tag(name = "文件上传", description = "提供图片上传功能")
@RestController
@RequestMapping("/api/upload")
public class FileUploadController {

    @Autowired
    private FileUploadService fileUploadService;

    /**
     * 上传图片
     * 权限：公开
     * 注意：所有文件处理逻辑已移至Service层
     */
    @Operation(summary = "上传图片", description = "上传图片文件，返回可访问的URL地址")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "上传成功"),
        @ApiResponse(responseCode = "400", description = "文件类型不支持或文件为空")
    })
    @PostMapping("/image")
    public ResponseEntity<ApiResult<String>> uploadImage(
            @Parameter(description = "图片文件", required = true)
            @RequestParam("file") MultipartFile file) {
        // 所有文件处理逻辑已移至Service层
        String fileUrl = fileUploadService.uploadImage(file);
        return ResponseEntity.ok(ApiResult.success(fileUrl, "图片上传成功"));
    }

    /**
     * 查询已上传图片列表
     * 权限：ADMIN
     * 注意：所有文件遍历和引用检查逻辑已移至Service层
     */
    @Operation(summary = "查询已上传图片列表", description = "列出uploads/images目录下的所有图片")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @SecurityRequirement(name = "JWT")
    @GetMapping("/images")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<List<ImageResourceVO>>> listImages(
            @Parameter(description = "是否只查询未引用的图片")
            @RequestParam(value = "onlyUnreferenced", required = false, defaultValue = "false") Boolean onlyUnreferenced) {
        // 所有文件遍历和引用检查逻辑已移至Service层
        List<ImageResourceVO> images = fileUploadService.listImages(onlyUnreferenced);
        return ResponseEntity.ok(ApiResult.success(images, "查询成功"));
    }

    /**
     * 删除所有未被真题引用的图片
     * 权限：ADMIN
     * 注意：所有文件删除逻辑已移至Service层
     */
    @Operation(summary = "删除所有未被真题引用的图片", description = "扫描真题引用后删除未被引用的图片")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "删除成功")
    })
    @SecurityRequirement(name = "JWT")
    @PostMapping("/images/cleanup")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<Integer>> cleanupUnreferencedImages() {
        // 所有文件删除逻辑已移至Service层
        int deleteCount = fileUploadService.cleanupUnreferencedImages();
        return ResponseEntity.ok(ApiResult.success(deleteCount, "已删除未引用图片 " + deleteCount + " 张"));
    }

    /**
     * 删除已上传图片
     * 权限：ADMIN
     * 注意：所有文件删除逻辑已移至Service层
     */
    @Operation(summary = "删除已上传图片", description = "根据文件名删除图片")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "删除成功"),
            @ApiResponse(responseCode = "400", description = "请求参数错误"),
            @ApiResponse(responseCode = "404", description = "文件不存在")
    })
    @SecurityRequirement(name = "JWT")
    @PostMapping("/image/delete")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<Void>> deleteImage(
            @Parameter(description = "文件名", required = true)
            @RequestParam String filename) {
        // 所有文件删除逻辑已移至Service层
        fileUploadService.deleteImage(filename);
        return ResponseEntity.ok(ApiResult.success(null, "删除成功"));
    }
}
