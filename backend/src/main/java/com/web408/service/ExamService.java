package com.web408.service;

import com.web408.pojo.dto.ExamQuestionCreateDTO;
import com.web408.pojo.dto.ExamQuestionUpdateDTO;
import com.web408.pojo.entity.ExamQuestion;
import com.web408.pojo.vo.ExamCategoryStatVO;
import com.web408.pojo.vo.ExamYearStatVO;
import com.web408.pojo.vo.ExportResultVO;
import com.web408.pojo.vo.PageVO;

import java.util.List;

/**
 * 真题服务接口
 * 提供真题查询和管理功能
 * 遵循单一职责原则：只处理真题相关业务
 */
public interface ExamService {

    /**
     * 分页查询真题（支持年份、分类、关键词筛选和排序）
     * 
     * @param page 页码（从1开始）
     * @param size 每页大小
     * @param year 年份（可选）
     * @param category 分类（可选）
     * @param subjectId 科目ID（可选）
     * @param noCategory 是否筛选无分类的题目（可选）
     * @param keyword 搜索关键词（可选，匹配title或content）
     * @param sortField 排序字段（可选）
     * @param sortOrder 排序方向（可选，asc/desc）
     * @return 分页响应对象
     */
    PageVO<ExamQuestion> findByPage(int page, int size, Integer year, String category, Long subjectId, Boolean noCategory, String keyword, String sortField, String sortOrder);

    /**
     * 查询所有真题
     * 仅用于内部统计或工具类功能
     *
     * @return 真题列表
     */
    List<ExamQuestion> findAll();

    /**
     * 根据ID查询真题详情
     * 
     * @param id 真题ID
     * @return ExamQuestion对象，不存在返回null
     */
    ExamQuestion findById(Long id);

    /**
     * 检查指定年份和题号的真题是否已存在
     * 用于创建前查重，返回已存在的完整记录信息供前端展示
     * 
     * @param year 年份
     * @param questionNumber 题号
     * @return ExamQuestion对象，不存在返回null
     */
    ExamQuestion checkDuplicate(Integer year, Integer questionNumber);

    /**
     * 创建真题（仅ADMIN）
     * 
     * @param request 创建请求DTO
     * @param authorId 作者ID
     * @return 创建后的真题对象
     */
    ExamQuestion create(ExamQuestionCreateDTO request, Long authorId);
    
    /**
     * 创建真题（自动获取当前用户）
     * 遵循KISS原则：Service层统一处理用户认证逻辑
     * 
     * @param request 创建请求DTO
     * @return 创建后的真题对象
     */
    ExamQuestion createWithCurrentUser(ExamQuestionCreateDTO request);

    /**
     * 更新真题（仅ADMIN）
     * 
     * @param request 更新请求DTO
     * @return 更新后的真题对象
     */
    ExamQuestion update(ExamQuestionUpdateDTO request);

    /**
     * 删除真题（仅ADMIN）
     * 
     * @param id 真题ID
     * @return 是否删除成功
     */
    boolean delete(Long id);

    /**
     * 根据年份查询所有真题（按题号排序）
     * 用于年份页面展示
     * 
     * @param year 年份
     * @param category 分类（可选）
     * @param subjectId 科目ID（可选）
     * @return 真题列表，按题号升序排列
     */
    List<ExamQuestion> findByYear(Integer year, String category, Long subjectId);

    /**
     * 根据科目ID查询该科目下实际存在真题的分类名称列表
     * 由后端统一聚合，前端仅负责展示
     *
     * @param subjectId 科目ID
     * @return 分类名称列表（去重且不包含空分类）
     */
    List<String> getCategoriesBySubject(Long subjectId);

    /**
     * 查询真题年份统计信息
     *
     * @param category 分类筛选（可选）
     * @return 每个年份对应的题目数量列表
     */
    List<ExamYearStatVO> getYearStats(String category);

    /**
     * 查询用于年份导航的真题索引数据
     * 仅返回ID、年份、题号、标题、分类等基本信息
     *
     * @param category 分类筛选（可选）
     * @return 真题列表（按年份降序、题号升序排序）
     */
    List<ExamQuestion> findAllForIndex(String category);

    /**
     * 按科目导出真题（支持Markdown格式）
     * 遵循KISS原则：Service层处理所有导出逻辑，Controller只负责返回文件流
     * 
     * @param subjectId 科目ID
     * @param format 导出格式（markdown）
     * @return 导出结果VO，包含文件字节、文件名和内容类型
     */
    ExportResultVO exportBySubject(Long subjectId, String format);

    /**
     * 查询真题分类统计信息（管理端）
     * 返回科目+分类的二维统计数据，按题目数量降序排列
     * 
     * @param subjectId 科目ID筛选（可选，为null时统计所有科目）
     * @return 分类统计列表
     */
    List<ExamCategoryStatVO> getCategoryStats(Long subjectId);

    /**
     * 根据科目和分类查询真题列表（用于分类统计导出时附带题目明细）
     *
     * @param subjectId 科目ID（可选，为null时不按科目限制）
     * @param category  分类名称
     * @return 真题列表（按年份降序、题号升序）
     */
    List<ExamQuestion> findBySubjectAndCategory(Long subjectId, String category);

}
