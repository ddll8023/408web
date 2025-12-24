package com.web408.controller;

import com.web408.pojo.dto.ExamQueryDTO;
import com.web408.pojo.dto.ExamQuestionCreateDTO;
import com.web408.pojo.dto.ExamQuestionUpdateDTO;
import com.web408.pojo.entity.ExamQuestion;
import com.web408.pojo.vo.ApiResult;
import com.web408.pojo.vo.ExamCategoryStatVO;
import com.web408.pojo.vo.ExamYearStatVO;
import com.web408.pojo.vo.ExportResultVO;
import com.web408.pojo.vo.PageVO;
import com.web408.service.ExamService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;

/**
 * 真题控制器
 * 用途：提供真题管理的RESTful API接口
 * 遵循KISS原则：简单清晰的接口设计，无业务逻辑
 * 
 * 职责边界：
 * - ✅ 接收HTTP请求参数
 * - ✅ 调用Service层方法
 * - ✅ 返回统一格式响应
 * - ❌ 禁止包含任何业务逻辑
 * 
 * 接口说明：
 * - GET /api/exam：分页查询真题
 * - GET /api/exam/{id}：根据ID查询真题详情
 * - GET /api/exam/check-duplicate：检查真题是否重复（ADMIN专用）
 * - POST /api/exam：创建真题（ADMIN专用）
 * - POST /api/exam/{id}：更新真题（ADMIN专用）
 * - POST /api/exam/{id}/delete：删除真题（ADMIN专用）
 * - GET /api/exam/year/{year}：根据年份查询真题列表
 * - GET /api/exam/categories/{subjectId}：查询科目下的分类列表
 * - GET /api/exam/year-stats：查询年份统计
 * - GET /api/exam/index：查询真题索引数据
 * - GET /api/exam/category-stats：查询分类统计
 * - GET /api/exam/by-category：根据科目和分类查询真题
 * - GET /api/exam/export：按科目导出真题
 * 
 * Source: springdoc-openapi 官方文档
 */
@Tag(name = "真题管理", description = "提供真题查询和管理功能")
@RestController
@RequestMapping("/api/exam")
public class ExamController {

    @Autowired
    private ExamService examService;

    /**
     * 分页查询真题
     * 权限：公开
     */
    @Operation(summary = "分页查询真题", description = "支持年份、分类、科目、关键词筛选和排序")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping
    public ResponseEntity<ApiResult<PageVO<ExamQuestion>>> findByPage(ExamQueryDTO query) {
        PageVO<ExamQuestion> result = examService.findByPage(
                query.getPage() != null ? query.getPage() : 1,
                query.getSize() != null ? query.getSize() : 10,
                query.getYear(),
                query.getCategory(),
                query.getSubjectId(),
                query.getNoCategory(),
                query.getKeyword(),
                query.getSortField(),
                query.getSortOrder());
        return ResponseEntity.ok(ApiResult.success(result, "查询成功"));
    }

    /**
     * 根据ID查询真题详情
     * 权限：公开
     */
    @Operation(summary = "查询真题详情", description = "根据ID查询真题详细信息")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/{id}")
    public ResponseEntity<ApiResult<ExamQuestion>> findById(
            @Parameter(description = "真题ID", required = true) @PathVariable Long id) {
        ExamQuestion exam = examService.findById(id);
        if (exam == null) {
            return ResponseEntity.status(404).body(ApiResult.error(404, "真题不存在"));
        }
        return ResponseEntity.ok(ApiResult.success(exam, "查询成功"));
    }

    /**
     * 检查真题是否重复
     * 权限：ADMIN
     */
    @Operation(summary = "检查真题重复", description = "检查指定年份和题号的真题是否已存在")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @SecurityRequirement(name = "JWT")
    @GetMapping("/check-duplicate")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<ExamQuestion>> checkDuplicate(
            @Parameter(description = "年份", required = true) @RequestParam Integer year,
            @Parameter(description = "题号", required = true) @RequestParam Integer questionNumber) {
        ExamQuestion existing = examService.checkDuplicate(year, questionNumber);
        return ResponseEntity.ok(ApiResult.success(existing, "查询成功"));
    }

    /**
     * 创建真题
     * 权限：ADMIN
     * 注意：用户ID由Service层从SecurityContext获取
     */
    @Operation(summary = "创建真题", description = "管理员创建新的真题")
    @ApiResponse(responseCode = "200", description = "创建成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<ExamQuestion>> create(
            @Parameter(description = "真题信息", required = true)
            @Valid @RequestBody ExamQuestionCreateDTO dto) {
        // 用户认证逻辑已移至Service层
        ExamQuestion created = examService.createWithCurrentUser(dto);
        return ResponseEntity.ok(ApiResult.success(created, "创建成功"));
    }

    /**
     * 更新真题
     * 权限：ADMIN
     */
    @Operation(summary = "更新真题", description = "管理员更新真题信息")
    @ApiResponse(responseCode = "200", description = "更新成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<ExamQuestion>> update(
            @Parameter(description = "真题ID", required = true) @PathVariable Long id,
            @Parameter(description = "真题信息", required = true)
            @Valid @RequestBody ExamQuestionUpdateDTO dto) {
        dto.setId(id);
        ExamQuestion updated = examService.update(dto);
        return ResponseEntity.ok(ApiResult.success(updated, "更新成功"));
    }

    /**
     * 删除真题
     * 权限：ADMIN
     */
    @Operation(summary = "删除真题", description = "管理员删除真题")
    @ApiResponse(responseCode = "200", description = "删除成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping("/{id}/delete")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<Void>> delete(
            @Parameter(description = "真题ID", required = true) @PathVariable Long id) {
        examService.delete(id);
        return ResponseEntity.ok(ApiResult.success(null, "删除成功"));
    }

    /**
     * 根据年份查询真题列表
     * 权限：公开
     */
    @Operation(summary = "根据年份查询真题", description = "查询指定年份的所有真题")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/year/{year}")
    public ResponseEntity<ApiResult<List<ExamQuestion>>> findByYear(
            @Parameter(description = "年份", required = true) @PathVariable Integer year,
            @Parameter(description = "分类") @RequestParam(required = false) String category,
            @Parameter(description = "科目ID") @RequestParam(required = false) Long subjectId) {
        List<ExamQuestion> list = examService.findByYear(year, category, subjectId);
        return ResponseEntity.ok(ApiResult.success(list, "查询成功"));
    }

    /**
     * 查询科目下的分类列表
     * 权限：公开
     */
    @Operation(summary = "查询科目下的分类", description = "查询指定科目下实际存在真题的分类列表")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/categories/{subjectId}")
    public ResponseEntity<ApiResult<List<String>>> getCategoriesBySubject(
            @Parameter(description = "科目ID", required = true) @PathVariable Long subjectId) {
        List<String> categories = examService.getCategoriesBySubject(subjectId);
        return ResponseEntity.ok(ApiResult.success(categories, "查询成功"));
    }

    /**
     * 查询年份统计
     * 权限：公开
     */
    @Operation(summary = "查询年份统计", description = "按年份统计真题数量")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/year-stats")
    public ResponseEntity<ApiResult<List<ExamYearStatVO>>> getYearStats(
            @Parameter(description = "分类筛选") @RequestParam(required = false) String category) {
        List<ExamYearStatVO> stats = examService.getYearStats(category);
        return ResponseEntity.ok(ApiResult.success(stats, "查询成功"));
    }

    /**
     * 查询真题索引数据
     * 权限：公开
     */
    @Operation(summary = "查询真题索引", description = "查询用于年份导航的真题索引数据")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/index")
    public ResponseEntity<ApiResult<List<ExamQuestion>>> findAllForIndex(
            @Parameter(description = "分类筛选") @RequestParam(required = false) String category) {
        List<ExamQuestion> list = examService.findAllForIndex(category);
        return ResponseEntity.ok(ApiResult.success(list, "查询成功"));
    }

    /**
     * 查询分类统计
     * 权限：公开
     */
    @Operation(summary = "查询分类统计", description = "按分类统计真题数量")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/category-stats")
    public ResponseEntity<ApiResult<List<ExamCategoryStatVO>>> getCategoryStats(
            @Parameter(description = "科目ID筛选") @RequestParam(required = false) Long subjectId) {
        List<ExamCategoryStatVO> stats = examService.getCategoryStats(subjectId);
        return ResponseEntity.ok(ApiResult.success(stats, "查询成功"));
    }

    /**
     * 根据科目和分类查询真题
     * 权限：公开
     */
    @Operation(summary = "根据科目和分类查询真题", description = "查询指定科目和分类的真题列表")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/by-category")
    public ResponseEntity<ApiResult<List<ExamQuestion>>> findBySubjectAndCategory(
            @Parameter(description = "科目ID") @RequestParam(required = false) Long subjectId,
            @Parameter(description = "分类名称", required = true) @RequestParam String category) {
        List<ExamQuestion> list = examService.findBySubjectAndCategory(subjectId, category);
        return ResponseEntity.ok(ApiResult.success(list, "查询成功"));
    }

    /**
     * 按科目导出真题
     * 权限：公开
     * 注意：所有导出逻辑已移至Service层
     */
    @Operation(summary = "导出真题", description = "按科目导出真题（支持Markdown格式）")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "导出成功"),
            @ApiResponse(responseCode = "400", description = "参数错误")
    })
    @GetMapping("/export")
    public ResponseEntity<byte[]> exportBySubject(
            @Parameter(description = "科目ID", required = true) @RequestParam Long subjectId,
            @Parameter(description = "导出格式", required = true) @RequestParam String format) {
        // 调用Service层处理导出逻辑
        ExportResultVO exportResult = examService.exportBySubject(subjectId, format);
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.parseMediaType(exportResult.getContentType()));
        headers.setContentDispositionFormData("attachment", 
                URLEncoder.encode(exportResult.getFilename(), StandardCharsets.UTF_8));
        headers.setContentLength(exportResult.getFileBytes().length);
        
        return ResponseEntity.ok().headers(headers).body(exportResult.getFileBytes());
    }
}
