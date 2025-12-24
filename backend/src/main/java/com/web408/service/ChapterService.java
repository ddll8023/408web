package com.web408.service;

import com.web408.pojo.dto.ChapterDTO;
import com.web408.pojo.vo.ChapterVO;

import java.util.List;

/**
 * 章节服务接口
 * 用途：章节管理的业务逻辑
 * 遵循SOLID原则：接口与实现分离
 */
public interface ChapterService {
    /**
     * 根据科目ID查询章节树（包含禁用的）
     * @param subjectId 科目ID
     * @return 章节VO树形列表
     */
    List<ChapterVO> getChapterTree(Long subjectId);

    /**
     * 根据科目ID查询启用的章节树
     * @param subjectId 科目ID
     * @return 章节VO树形列表
     */
    List<ChapterVO> getEnabledChapterTree(Long subjectId);

    /**
     * 根据ID查询章节
     * @param id 章节ID
     * @return 章节VO
     */
    ChapterVO getChapterById(Long id);

    /**
     * 创建章节
     * @param request 章节请求DTO
     * @return 创建的章节VO
     */
    ChapterVO createChapter(ChapterDTO request);

    /**
     * 更新章节
     * @param id 章节ID
     * @param request 章节请求DTO
     * @return 更新后的章节VO
     */
    ChapterVO updateChapter(Long id, ChapterDTO request);

    /**
     * 删除章节
     * @param id 章节ID
     */
    void deleteChapter(Long id);
}

