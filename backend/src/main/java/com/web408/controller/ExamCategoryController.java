package com.web408.controller;

import com.web408.pojo.dto.ExamCategoryDTO;
import com.web408.pojo.vo.ApiResult;
import com.web408.pojo.vo.ExamCategoryVO;
import com.web408.service.ExamCategoryService;
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
 * 分类标签控制器
 * 用途：提供分类标签管理的RESTful API接口
 * 遵循KISS原则：简单清晰的接口设计
 * 
 * 接口说明：
 * - GET /api/exam-category：查询所有分类（包含引用统计）
 * - GET /api/exam-category/subject/{subjectId}：按科目查询所有分类
 * - GET /api/exam-category/subject/{subjectId}/enabled：按科目查询启用的分类
 * - GET /api/exam-category/subject/{subjectId}/tree：按科目查询分类树形结构
 * - GET /api/exam-category/subject/{subjectId}/tree/enabled：按科目查询启用的分类树形结构
 * - GET /api/exam-category/available-parents：查询可作为父分类的列表（ADMIN专用）
 * - GET /api/exam-category/{id}：根据ID查询分类
 * - POST /api/exam-category：创建分类（ADMIN专用）
 * - POST /api/exam-category/{id}：更新分类（ADMIN专用）
 * - POST /api/exam-category/{id}/delete：删除分类（ADMIN专用）
 * - GET /api/exam-category/{id}/usage：检查分类是否被引用（ADMIN专用）
 * 
 * Source: springdoc-openapi 官方文档
 */
@Tag(name = "分类标签管理", description = "提供分类标签查询和管理功能")
@RestController
@RequestMapping("/api/exam-category")
public class ExamCategoryController {

    @Autowired
    private ExamCategoryService examCategoryService;

    /**
     * 查询所有分类（包含引用统计）
     * 权限：公开
     * @param questionType 题目类型：exam=真题, mock=模拟题, exercise=课后习题（默认exam）
     */
    @Operation(summary = "查询所有分类", description = "查询所有分类（包含引用统计），可按题目类型筛选")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping
    public ResponseEntity<ApiResult<List<ExamCategoryVO>>> getAllCategories(
            @Parameter(description = "题目类型：exam=真题, mock=模拟题, exercise=课后习题")
            @RequestParam(required = false, defaultValue = "exam") String questionType) {
        List<ExamCategoryVO> categories = examCategoryService.getAllCategories(questionType);
        return ResponseEntity.ok(ApiResult.success(categories, "查询成功"));
    }

    /**
     * 按科目查询所有分类
     * 权限：公开
     * @param questionType 题目类型：exam=真题, mock=模拟题, exercise=课后习题（默认exam）
     */
    @Operation(summary = "按科目查询分类", description = "按科目查询所有分类（包含引用统计），可按题目类型筛选")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/subject/{subjectId}")
    public ResponseEntity<ApiResult<List<ExamCategoryVO>>> getCategoriesBySubject(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long subjectId,
            @Parameter(description = "题目类型：exam=真题, mock=模拟题, exercise=课后习题")
            @RequestParam(required = false, defaultValue = "exam") String questionType) {
        List<ExamCategoryVO> categories = examCategoryService.getCategoriesBySubject(subjectId, questionType);
        return ResponseEntity.ok(ApiResult.success(categories, "查询成功"));
    }

    /**
     * 按科目查询启用的分类
     * 权限：公开
     */
    @Operation(summary = "查询启用分类", description = "按科目查询启用的分类（用于前端选择器）")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/subject/{subjectId}/enabled")
    public ResponseEntity<ApiResult<List<ExamCategoryVO>>> getEnabledCategoriesBySubject(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long subjectId) {
        List<ExamCategoryVO> categories = examCategoryService.getEnabledCategoriesBySubject(subjectId);
        return ResponseEntity.ok(ApiResult.success(categories, "查询成功"));
    }

    /**
     * 按科目查询分类树形结构
     * 权限：公开
     */
    @Operation(summary = "查询分类树", description = "按科目查询分类树形结构")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/subject/{subjectId}/tree")
    public ResponseEntity<ApiResult<List<ExamCategoryVO>>> getCategoryTreeBySubject(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long subjectId) {
        List<ExamCategoryVO> categories = examCategoryService.getCategoryTreeBySubject(subjectId);
        return ResponseEntity.ok(ApiResult.success(categories, "查询成功"));
    }

    /**
     * 按科目查询启用的分类树形结构
     * 权限：公开
     */
    @Operation(summary = "查询启用分类树", description = "按科目查询启用的分类树形结构（用于前端侧边栏）")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/subject/{subjectId}/tree/enabled")
    public ResponseEntity<ApiResult<List<ExamCategoryVO>>> getEnabledCategoryTreeBySubject(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long subjectId) {
        List<ExamCategoryVO> categories = examCategoryService.getEnabledCategoryTreeBySubject(subjectId);
        return ResponseEntity.ok(ApiResult.success(categories, "查询成功"));
    }

    /**
     * 按科目和题型查询启用的分类树形结构（带题型特定统计）
     * 权限：公开
     * 用途：模拟题和课后习题侧边栏使用
     */
    @Operation(summary = "查询启用分类树（带题型统计）", description = "按科目和题型查询启用的分类树形结构，questionCount为指定题型的数量")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/subject/{subjectId}/tree/enabled/{questionType}")
    public ResponseEntity<ApiResult<List<ExamCategoryVO>>> getEnabledCategoryTreeWithStatsBySubject(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long subjectId,
            @Parameter(description = "题目类型：exam=真题, mock=模拟题, exercise=课后习题", required = true)
            @PathVariable String questionType) {
        List<ExamCategoryVO> categories = examCategoryService.getEnabledCategoryTreeWithStatsBySubject(subjectId, questionType);
        return ResponseEntity.ok(ApiResult.success(categories, "查询成功"));
    }

    /**
     * 查询可作为父分类的列表
     * 权限：ADMIN
     */
    @Operation(summary = "查询可选父分类", description = "查询可作为父分类的列表（顶级分类，排除自身及其子孙）")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @SecurityRequirement(name = "JWT")
    @GetMapping("/available-parents")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<List<ExamCategoryVO>>> getAvailableParentCategories(
            @Parameter(description = "科目ID", required = true) @RequestParam Long subjectId,
            @Parameter(description = "排除的分类ID") @RequestParam(required = false) Long excludeId) {
        List<ExamCategoryVO> categories = examCategoryService.getAvailableParentCategories(subjectId, excludeId);
        return ResponseEntity.ok(ApiResult.success(categories, "查询成功"));
    }

    /**
     * 根据ID查询分类
     * 权限：公开
     */
    @Operation(summary = "查询分类详情", description = "根据ID查询分类详细信息")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/{id}")
    public ResponseEntity<ApiResult<ExamCategoryVO>> getCategoryById(
            @Parameter(description = "分类ID", required = true)
            @PathVariable Long id) {
        ExamCategoryVO category = examCategoryService.getCategoryById(id);
        return ResponseEntity.ok(ApiResult.success(category, "查询成功"));
    }

    /**
     * 创建分类
     * 权限：ADMIN
     */
    @Operation(summary = "创建分类", description = "创建新分类，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "创建成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<ExamCategoryVO>> createCategory(
            @Parameter(description = "分类信息", required = true)
            @Valid @RequestBody ExamCategoryDTO request) {
        ExamCategoryVO category = examCategoryService.createCategory(request);
        return ResponseEntity.ok(ApiResult.success(category, "创建成功"));
    }

    /**
     * 更新分类
     * 权限：ADMIN
     */
    @Operation(summary = "更新分类", description = "更新指定分类的信息，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "更新成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<ExamCategoryVO>> updateCategory(
            @Parameter(description = "分类ID", required = true)
            @PathVariable Long id,
            @Parameter(description = "分类信息", required = true)
            @Valid @RequestBody ExamCategoryDTO request) {
        ExamCategoryVO category = examCategoryService.updateCategory(id, request);
        return ResponseEntity.ok(ApiResult.success(category, "更新成功"));
    }

    /**
     * 删除分类
     * 权限：ADMIN
     */
    @Operation(summary = "删除分类", description = "删除指定分类，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "删除成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping("/{id}/delete")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<Void>> deleteCategory(
            @Parameter(description = "分类ID", required = true)
            @PathVariable Long id) {
        examCategoryService.deleteCategory(id);
        return ResponseEntity.ok(ApiResult.success(null, "删除成功"));
    }

    /**
     * 检查分类是否被引用
     * 权限：ADMIN
     */
    @Operation(summary = "检查分类引用", description = "检查分类是否被引用，返回引用数量")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @SecurityRequirement(name = "JWT")
    @GetMapping("/{id}/usage")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<Integer>> checkCategoryUsage(
            @Parameter(description = "分类ID", required = true)
            @PathVariable Long id) {
        int usage = examCategoryService.checkCategoryUsage(id);
        return ResponseEntity.ok(ApiResult.success(usage, "查询成功"));
    }

    /**
     * 获取分类统计信息（去重后的题目数）
     * 用于解决一道题目有多个标签时的重复计数问题
     * 权限：公开
     */
    @Operation(summary = "获取分类统计", description = "获取各科目去重后的题目数统计，解决多标签重复计数问题")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/stats")
    public ResponseEntity<ApiResult<java.util.Map<String, Object>>> getCategoryStats(
            @Parameter(description = "题目类型：exam=真题, mock=模拟题, exercise=课后习题")
            @RequestParam(required = false, defaultValue = "exam") String questionType) {
        java.util.Map<String, Object> stats = examCategoryService.getCategoryStats(questionType);
        return ResponseEntity.ok(ApiResult.success(stats, "查询成功"));
    }
}
