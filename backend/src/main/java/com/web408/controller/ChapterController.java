package com.web408.controller;

import com.web408.pojo.dto.ChapterDTO;
import com.web408.pojo.vo.ApiResult;
import com.web408.pojo.vo.ChapterVO;
import com.web408.service.ChapterService;
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
 * 章节控制器
 * 提供章节管理的RESTful API接口
 * 遵循KISS原则：简单清晰的接口设计
 */
@Tag(name = "章节管理", description = "提供章节查询和管理功能")
@RestController
@RequestMapping("/api/chapter")
public class ChapterController {

    @Autowired
    private ChapterService chapterService;

    /**
     * 查询科目的启用章节树
     * 权限：公开
     */
    @Operation(summary = "查询启用章节树", description = "根据科目ID查询该科目下所有启用的章节（树形结构）")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/subject/{subjectId}")
    public ResponseEntity<ApiResult<List<ChapterVO>>> getEnabledChapterTree(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long subjectId) {
        List<ChapterVO> chapters = chapterService.getEnabledChapterTree(subjectId);
        return ResponseEntity.ok(ApiResult.success(chapters, "查询成功"));
    }

    /**
     * 查询科目的所有章节树（包含禁用）
     * 权限：ADMIN
     */
    @Operation(summary = "查询所有章节树", description = "根据科目ID查询该科目下所有章节（包含禁用状态），仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @SecurityRequirement(name = "JWT")
    @GetMapping("/subject/{subjectId}/all")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<List<ChapterVO>>> getChapterTree(
            @Parameter(description = "科目ID", required = true)
            @PathVariable Long subjectId) {
        List<ChapterVO> chapters = chapterService.getChapterTree(subjectId);
        return ResponseEntity.ok(ApiResult.success(chapters, "查询成功"));
    }

    /**
     * 根据ID查询章节
     * 权限：公开
     */
    @Operation(summary = "查询章节详情", description = "根据章节ID查询章节详细信息")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/{id}")
    public ResponseEntity<ApiResult<ChapterVO>> getChapterById(
            @Parameter(description = "章节ID", required = true)
            @PathVariable Long id) {
        ChapterVO chapter = chapterService.getChapterById(id);
        return ResponseEntity.ok(ApiResult.success(chapter, "查询成功"));
    }

    /**
     * 创建章节
     * 权限：ADMIN
     */
    @Operation(summary = "创建章节", description = "创建新章节，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "创建成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<ChapterVO>> createChapter(
            @Parameter(description = "章节信息", required = true)
            @Valid @RequestBody ChapterDTO request) {
        ChapterVO chapter = chapterService.createChapter(request);
        return ResponseEntity.ok(ApiResult.success(chapter, "创建成功"));
    }

    /**
     * 更新章节
     * 权限：ADMIN
     */
    @Operation(summary = "更新章节", description = "更新指定章节的信息，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "更新成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<ChapterVO>> updateChapter(
            @Parameter(description = "章节ID", required = true)
            @PathVariable Long id,
            @Parameter(description = "章节信息", required = true)
            @Valid @RequestBody ChapterDTO request) {
        ChapterVO chapter = chapterService.updateChapter(id, request);
        return ResponseEntity.ok(ApiResult.success(chapter, "更新成功"));
    }

    /**
     * 删除章节
     * 权限：ADMIN
     */
    @Operation(summary = "删除章节", description = "删除指定章节，仅管理员可访问")
    @ApiResponse(responseCode = "200", description = "删除成功")
    @SecurityRequirement(name = "JWT")
    @PostMapping("/{id}/delete")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResult<Void>> deleteChapter(
            @Parameter(description = "章节ID", required = true)
            @PathVariable Long id) {
        chapterService.deleteChapter(id);
        return ResponseEntity.ok(ApiResult.success(null, "删除成功"));
    }
}
