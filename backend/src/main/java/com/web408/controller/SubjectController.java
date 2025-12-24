package com.web408.controller;

import com.web408.pojo.dto.SubjectDTO;
import com.web408.pojo.vo.ApiResult;
import com.web408.pojo.vo.SubjectVO;
import com.web408.service.SubjectService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 科目控制器
 * 用途：提供科目管理的RESTful API接口
 * 遵循KISS原则：简单清晰的接口设计
 * 
 * 接口说明：
 * - GET /api/subject：查询所有启用的科目
 * - GET /api/subject/all：查询所有科目（包含禁用，ADMIN专用）
 * - GET /api/subject/{id}：根据ID查询科目
 * - GET /api/subject/code/{code}：根据编码查询科目
 * - POST /api/subject：创建科目（ADMIN专用）
 * - POST /api/subject/{id}：更新科目（ADMIN专用）
 * - POST /api/subject/{id}/delete：删除科目（ADMIN专用）
 * 
 * Source: springdoc-openapi 官方文档
 */
@Tag(name = "科目管理", description = "提供科目查询和管理功能")
@RestController
@RequestMapping("/api/subject")
public class SubjectController {

    @Autowired
    private SubjectService subjectService;

    /**
     * 查询所有启用的科目
     * 权限：公开
     */
    @Operation(summary = "查询启用科目列表", description = "查询所有启用状态的科目")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping
    public ResponseEntity<ApiResult<List<SubjectVO>>> getEnabledSubjects() {
        List<SubjectVO> subjects = subjectService.getEnabledSubjects();
        return ResponseEntity.ok(ApiResult.success(subjects, "查询成功"));
    }

    /**
     * 查询所有科目（包含禁用）
     * 权限：ADMIN
     */
    @Operation(summary = "查询所有科目", description = "查询所有科目（包含禁用状态），仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @SecurityRequirement(name = "JWT")
    @GetMapping("/all")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<List<SubjectVO>>> getAllSubjects() {
        List<SubjectVO> subjects = subjectService.getAllSubjects();
        return ResponseEntity.ok(ApiResult.success(subjects, "查询成功"));
    }

    /**
     * 根据ID查询科目
     * 权限：公开
     */
    @Operation(summary = "查询科目详情", description = "根据ID查询科目详细信息")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/{id}")
    public ResponseEntity<ApiResult<SubjectVO>> getSubjectById(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long id) {
        SubjectVO subject = subjectService.getSubjectById(id);
        return ResponseEntity.ok(ApiResult.success(subject, "查询成功"));
    }

    /**
     * 根据编码查询科目
     * 权限：公开
     */
    @Operation(summary = "根据编码查询科目", description = "根据科目编码查询科目信息")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/code/{code}")
    public ResponseEntity<ApiResult<SubjectVO>> getSubjectByCode(
            @Parameter(description = "科目编码", required = true)
            @PathVariable String code) {
        SubjectVO subject = subjectService.getSubjectByCode(code);
        return ResponseEntity.ok(ApiResult.success(subject, "查询成功"));
    }

    /**
     * 创建科目
     * 权限：ADMIN
     */
    @Operation(summary = "创建科目", description = "创建新科目，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "创建成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<SubjectVO>> createSubject(
            @Parameter(description = "科目信息", required = true)
            @Valid @RequestBody SubjectDTO request) {
        SubjectVO subject = subjectService.createSubject(request);
        return ResponseEntity.ok(ApiResult.success(subject, "创建成功"));
    }

    /**
     * 更新科目
     * 权限：ADMIN
     */
    @Operation(summary = "更新科目", description = "更新指定科目的信息，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "更新成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<SubjectVO>> updateSubject(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long id,
            @Parameter(description = "科目信息", required = true)
            @Valid @RequestBody SubjectDTO request) {
        SubjectVO subject = subjectService.updateSubject(id, request);
        return ResponseEntity.ok(ApiResult.success(subject, "更新成功"));
    }

    /**
     * 删除科目
     * 权限：ADMIN
     */
    @Operation(summary = "删除科目", description = "删除指定科目，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "删除成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping("/{id}/delete")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<Void>> deleteSubject(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long id) {
        subjectService.deleteSubject(id);
        return ResponseEntity.ok(ApiResult.success(null, "删除成功"));
    }
}
