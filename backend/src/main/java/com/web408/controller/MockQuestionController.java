package com.web408.controller;

import com.web408.pojo.dto.MockQuestionCreateDTO;
import com.web408.pojo.dto.MockQuestionUpdateDTO;
import com.web408.pojo.entity.MockQuestion;
import com.web408.pojo.vo.ApiResult;
import com.web408.pojo.vo.CategoryStatVO;
import com.web408.pojo.vo.PageVO;
import com.web408.service.MockQuestionService;
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
import java.util.Map;

/**
 * 模拟题控制器
 * 用途：提供模拟题的增删改查接口
 * 遵循KISS原则：简洁的REST API设计，无业务逻辑
 * 
 * 职责边界：
 * - ✅ 接收HTTP请求参数
 * - ✅ 调用Service层方法
 * - ✅ 返回统一格式响应
 * - ❌ 禁止包含任何业务逻辑
 * 
 * 接口说明：
 * - POST /api/mock：创建模拟题（ADMIN专用）
 * - GET /api/mock/{id}：根据ID查询模拟题
 * - POST /api/mock/{id}：更新模拟题（ADMIN专用）
 * - POST /api/mock/{id}/delete：删除模拟题（ADMIN专用）
 * - GET /api/mock：分页查询模拟题
 * - GET /api/mock/source/{source}：根据来源查询模拟题列表
 * - GET /api/mock/source-stats：查询来源统计
 * - GET /api/mock/sources：查询所有来源机构列表
 * - GET /api/mock/categories/{subjectId}：根据科目查询分类列表
 * - GET /api/mock/subject-stats：按科目统计模拟题数量
 * 
 * Source: springdoc-openapi 官方文档
 */
@RestController
@RequestMapping("/api/mock")
@Tag(name = "模拟题管理", description = "模拟题增删改查接口")
public class MockQuestionController {
    
    @Autowired
    private MockQuestionService mockQuestionService;

    /**
     * 创建模拟题
     * 权限：ADMIN
     * 注意：用户认证和DTO转换逻辑已移至Service层
     */
    @Operation(summary = "创建模拟题", description = "管理员创建新的模拟题")
    @ApiResponse(responseCode = "200", description = "创建成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<MockQuestion>> create(
            @Parameter(description = "模拟题信息", required = true)
            @Valid @RequestBody MockQuestionCreateDTO dto) {
        // 用户认证和DTO转换逻辑已移至Service层
        MockQuestion created = mockQuestionService.createWithCurrentUser(dto);
        return ResponseEntity.ok(ApiResult.success(created, "创建成功"));
    }

    /**
     * 根据ID查询模拟题
     * 权限：公开
     */
    @Operation(summary = "查询模拟题详情", description = "根据ID查询单个模拟题")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/{id}")
    public ResponseEntity<ApiResult<MockQuestion>> findById(
            @Parameter(description = "模拟题ID", required = true) @PathVariable Long id) {
        MockQuestion mockQuestion = mockQuestionService.findById(id);
        if (mockQuestion == null) {
            return ResponseEntity.status(404).body(ApiResult.error(404, "模拟题不存在"));
        }
        return ResponseEntity.ok(ApiResult.success(mockQuestion, "查询成功"));
    }

    /**
     * 更新模拟题
     * 权限：ADMIN
     * 注意：DTO转换逻辑已移至Service层
     */
    @Operation(summary = "更新模拟题", description = "管理员更新模拟题信息")
    @ApiResponse(responseCode = "200", description = "更新成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<MockQuestion>> update(
            @Parameter(description = "模拟题ID", required = true) @PathVariable Long id,
            @Parameter(description = "模拟题信息", required = true)
            @Valid @RequestBody MockQuestionUpdateDTO dto) {
        // DTO转换逻辑已移至Service层
        MockQuestion updated = mockQuestionService.updateByDTO(id, dto);
        return ResponseEntity.ok(ApiResult.success(updated, "更新成功"));
    }

    /**
     * 删除模拟题
     * 权限：ADMIN
     */
    @Operation(summary = "删除模拟题", description = "管理员删除模拟题")
    @ApiResponse(responseCode = "200", description = "删除成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping("/{id}/delete")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<Void>> delete(
            @Parameter(description = "模拟题ID", required = true) @PathVariable Long id) {
        mockQuestionService.delete(id);
        return ResponseEntity.ok(ApiResult.success(null, "删除成功"));
    }

    /**
     * 分页查询模拟题
     * 权限：公开
     */
    @Operation(summary = "分页查询模拟题", description = "支持来源、分类、科目、关键词筛选和排序")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping
    public ResponseEntity<ApiResult<PageVO<MockQuestion>>> findByPage(
            @Parameter(description = "页码") @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页大小") @RequestParam(defaultValue = "10") int size,
            @Parameter(description = "来源机构") @RequestParam(required = false) String source,
            @Parameter(description = "分类") @RequestParam(required = false) String category,
            @Parameter(description = "科目ID") @RequestParam(required = false) Long subjectId,
            @Parameter(description = "是否筛选无分类") @RequestParam(required = false) Boolean noCategory,
            @Parameter(description = "搜索关键词") @RequestParam(required = false) String keyword,
            @Parameter(description = "排序字段") @RequestParam(required = false) String sortField,
            @Parameter(description = "排序方向") @RequestParam(required = false) String sortOrder) {
        PageVO<MockQuestion> result = mockQuestionService.findByPage(page, size, source, category, 
                                                                      subjectId, noCategory, keyword, sortField, sortOrder);
        return ResponseEntity.ok(ApiResult.success(result, "查询成功"));
    }

    /**
     * 根据来源查询模拟题列表
     * 权限：公开
     */
    @Operation(summary = "根据来源查询模拟题", description = "查询指定来源机构的所有模拟题")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/source/{source}")
    public ResponseEntity<ApiResult<List<MockQuestion>>> findBySource(
            @Parameter(description = "来源机构", required = true) @PathVariable String source,
            @Parameter(description = "分类") @RequestParam(required = false) String category,
            @Parameter(description = "科目ID") @RequestParam(required = false) Long subjectId) {
        List<MockQuestion> list = mockQuestionService.findBySource(source, category, subjectId);
        return ResponseEntity.ok(ApiResult.success(list, "查询成功"));
    }

    /**
     * 查询来源统计
     * 权限：公开
     */
    @Operation(summary = "查询来源统计", description = "按来源机构统计模拟题数量")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/source-stats")
    public ResponseEntity<ApiResult<List<Map<String, Object>>>> getSourceStats(
            @Parameter(description = "分类筛选") @RequestParam(required = false) String category) {
        List<Map<String, Object>> stats = mockQuestionService.getSourceStats(category);
        return ResponseEntity.ok(ApiResult.success(stats, "查询成功"));
    }

    /**
     * 查询所有来源机构列表
     * 权限：公开
     */
    @Operation(summary = "查询所有来源机构", description = "获取所有不重复的来源机构列表")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/sources")
    public ResponseEntity<ApiResult<List<String>>> getAllSources() {
        List<String> sources = mockQuestionService.getAllSources();
        return ResponseEntity.ok(ApiResult.success(sources, "查询成功"));
    }

    /**
     * 根据科目查询分类列表
     * 权限：公开
     */
    @Operation(summary = "查询科目下的分类", description = "查询指定科目下实际存在模拟题的分类列表")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/categories/{subjectId}")
    public ResponseEntity<ApiResult<List<String>>> findCategoriesBySubject(
            @Parameter(description = "科目ID", required = true) @PathVariable Long subjectId) {
        List<String> categories = mockQuestionService.findCategoriesBySubject(subjectId);
        return ResponseEntity.ok(ApiResult.success(categories, "查询成功"));
    }

    /**
     * 根据科目查询分类列表（带题目数量统计）
     * 权限：公开
     */
    @Operation(summary = "查询科目下的分类（带统计）", description = "查询指定科目下实际存在模拟题的分类列表，包含每个分类的题目数量")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/category-stats/{subjectId}")
    public ResponseEntity<ApiResult<List<CategoryStatVO>>> findCategoryStatsBySubject(
            @Parameter(description = "科目ID", required = true) @PathVariable Long subjectId) {
        List<CategoryStatVO> categories = mockQuestionService.findCategoryStatsBySubject(subjectId);
        return ResponseEntity.ok(ApiResult.success(categories, "查询成功"));
    }

    /**
     * 按科目统计模拟题数量
     * 权限：公开
     */
    @Operation(summary = "按科目统计数量", description = "按科目分组统计模拟题数量")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/subject-stats")
    public ResponseEntity<ApiResult<List<Map<String, Object>>>> countBySubject() {
        List<Map<String, Object>> stats = mockQuestionService.countBySubject();
        return ResponseEntity.ok(ApiResult.success(stats, "查询成功"));
    }

    /**
     * 根据来源查询标题列表
     * 权限：公开
     * 用途：编辑模拟题时，根据选择的来源动态加载标题下拉选项
     */
    @Operation(summary = "根据来源查询标题列表", description = "获取指定来源下所有不重复的标题列表")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/titles/{source}")
    public ResponseEntity<ApiResult<List<String>>> getTitlesBySource(
            @Parameter(description = "来源机构", required = true) @PathVariable String source) {
        List<String> titles = mockQuestionService.getTitlesBySource(source);
        return ResponseEntity.ok(ApiResult.success(titles, "查询成功"));
    }
}
