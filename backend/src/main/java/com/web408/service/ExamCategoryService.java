package com.web408.service;

import com.web408.pojo.dto.ExamCategoryDTO;
import com.web408.pojo.vo.ExamCategoryVO;

import java.util.List;

/**
 * 分类标签服务接口
 * 用途：分类标签管理的业务逻辑
 * 遵循SOLID原则：接口与实现分离
 */
public interface ExamCategoryService {

    /**
     * 查询所有分类（包含引用统计）
     * @param questionType 题目类型：exam=真题, mock=模拟题, exercise=课后习题
     * @return 分类VO列表
     */
    List<ExamCategoryVO> getAllCategories(String questionType);

    /**
     * 按科目查询所有分类（包含引用统计）
     * @param subjectId 科目ID
     * @param questionType 题目类型：exam=真题, mock=模拟题, exercise=课后习题
     * @return 分类VO列表
     */
    List<ExamCategoryVO> getCategoriesBySubject(Long subjectId, String questionType);

    /**
     * 按科目查询启用的分类（用于前端选择器）
     * @param subjectId 科目ID
     * @return 分类VO列表
     */
    List<ExamCategoryVO> getEnabledCategoriesBySubject(Long subjectId);

    /**
     * 按科目查询分类树形结构
     * @param subjectId 科目ID
     * @return 树形结构分类VO列表（顶级分类包含children）
     */
    List<ExamCategoryVO> getCategoryTreeBySubject(Long subjectId);

    /**
     * 按科目查询启用的分类树形结构（用于前端侧边栏）
     * @param subjectId 科目ID
     * @return 树形结构分类VO列表
     */
    List<ExamCategoryVO> getEnabledCategoryTreeBySubject(Long subjectId);

    /**
     * 按科目和题型查询启用的分类树形结构（带题型特定统计）
     * 用途：模拟题和课后习题侧边栏需要显示各自的题目数量
     * @param subjectId 科目ID
     * @param questionType 题目类型：exam=真题, mock=模拟题, exercise=课后习题
     * @return 树形结构分类VO列表（questionCount 为指定题型的数量）
     */
    List<ExamCategoryVO> getEnabledCategoryTreeWithStatsBySubject(Long subjectId, String questionType);

    /**
     * 查询可作为父分类的列表（顶级分类，排除自身及其子孙）
     * @param subjectId 科目ID
     * @param excludeId 排除的分类ID（编辑时排除自身）
     * @return 可选父分类列表
     */
    List<ExamCategoryVO> getAvailableParentCategories(Long subjectId, Long excludeId);

    /**
     * 根据ID查询分类
     * @param id 分类ID
     * @return 分类VO
     */
    ExamCategoryVO getCategoryById(Long id);

    /**
     * 创建分类
     * @param request 分类请求DTO
     * @return 创建的分类VO
     */
    ExamCategoryVO createCategory(ExamCategoryDTO request);

    /**
     * 更新分类
     * @param id 分类ID
     * @param request 分类请求DTO
     * @return 更新后的分类VO
     */
    ExamCategoryVO updateCategory(Long id, ExamCategoryDTO request);

    /**
     * 删除分类
     * @param id 分类ID
     */
    void deleteCategory(Long id);

    /**
     * 检查分类是否被引用
     * @param id 分类ID
     * @return 引用数量
     */
    int checkCategoryUsage(Long id);

    /**
     * 获取分类统计信息（去重后的题目数）
     * 用于解决一道题目有多个标签时的重复计数问题
     * @param questionType 题目类型：exam=真题, mock=模拟题, exercise=课后习题
     * @return 统计信息Map，包含各科目的去重题目数和总数
     */
    java.util.Map<String, Object> getCategoryStats(String questionType);
}
