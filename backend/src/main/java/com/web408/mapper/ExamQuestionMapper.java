package com.web408.mapper;

import com.web408.pojo.entity.ExamQuestion;
import com.web408.pojo.vo.ExamCategoryStatVO;
import com.web408.pojo.vo.ExamYearStatVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 真题Mapper接口
 */
@Mapper
public interface ExamQuestionMapper {
    
    /**
     * 插入真题
     * 
     * @param examQuestion 真题对象
     * @return 影响行数
     */
    int insert(ExamQuestion examQuestion);

    /**
     * 根据ID查询真题
     * 
     * @param id 真题ID
     * @return ExamQuestion对象，不存在返回null
     */
    ExamQuestion findById(@Param("id") Long id);

    /**
     * 根据年份和题号查询真题（用于唯一性校验）
     * 
     * @param year 年份
     * @param questionNumber 题号
     * @return ExamQuestion对象，不存在返回null
     */
    ExamQuestion findByYearAndNumber(@Param("year") Integer year, 
                                     @Param("questionNumber") Integer questionNumber);

    /**
     * 查询所有真题
     * 
     * @return 真题列表
     */
    List<ExamQuestion> findAll();

    /**
     * 根据年份查询真题
     * 
     * @param year 年份
     * @return 真题列表
     */
    List<ExamQuestion> findByYear(@Param("year") Integer year,
                                  @Param("category") String category,
                                  @Param("subjectId") Long subjectId);

    /**
     * 根据分类查询真题
     * 
     * @param category 分类
     * @return 真题列表
     */
    List<ExamQuestion> findByCategory(@Param("category") String category);

    /**
     * 根据科目和分类查询真题列表（用于分类统计导出）
     *
     * @param subjectId 科目ID（可选，为null时不按科目限制）
     * @param category  分类名称
     * @return 真题列表
     */
    List<ExamQuestion> findBySubjectAndCategory(@Param("subjectId") Long subjectId,
                                                @Param("category") String category);

    /**
     * 更新真题
     * 
     * @param examQuestion 真题对象
     * @return 影响行数
     */
    int update(ExamQuestion examQuestion);

    /**
     * 删除真题
     * 
     * @param id 真题ID
     * @return 影响行数
     */
    int deleteById(@Param("id") Long id);
    
    List<ExamQuestion> findAllForIndex(@Param("category") String category);
    
    /**
     * 分页查询真题（支持年份、分类、关键词筛选和排序）
     * 
     * @param offset 偏移量
     * @param limit 每页大小
     * @param year 年份（可选）
     * @param category 分类（可选）
     * @param subjectId 科目ID（可选）
     * @param noCategory 是否筛选无分类的题目（可选）
     * @param keyword 搜索关键词（可选，匹配title或content）
     * @param sortField 排序字段（可选）
     * @param sortOrder 排序方向（可选）
     * @return 真题列表
     */
    List<ExamQuestion> findByPage(@Param("offset") int offset, 
                                   @Param("limit") int limit, 
                                   @Param("year") Integer year,
                                   @Param("category") String category,
                                   @Param("subjectId") Long subjectId,
                                   @Param("noCategory") Boolean noCategory,
                                   @Param("keyword") String keyword,
                                   @Param("sortField") String sortField,
                                   @Param("sortOrder") String sortOrder);
    
    /**
     * 统计真题总数（支持年份、分类、科目、关键词筛选）
     * 
     * @param year 年份（可选）
     * @param category 分类（可选）
     * @param subjectId 科目ID（可选）
     * @param noCategory 是否筛选无分类的题目（可选）
     * @param keyword 搜索关键词（可选，匹配title或content）
     * @return 总记录数
     */
    long count(@Param("year") Integer year,
               @Param("category") String category,
               @Param("subjectId") Long subjectId,
               @Param("noCategory") Boolean noCategory,
               @Param("keyword") String keyword);

    /**
     * 根据科目ID查询该科目下实际存在真题的分类列表
     * 由后端统一聚合，避免前端自行筛选
     *
     * @param subjectId 科目ID
     * @return 分类名称列表（去重且不包含空分类）
     */
    List<String> findCategoriesBySubject(@Param("subjectId") Long subjectId);

    List<ExamYearStatVO> findYearStats(@Param("category") String category);

    /**
     * 查询指定科目的所有真题（用于导出）
     * 按年份降序、题号升序排序
     * 
     * @param subjectId 科目ID
     * @return 真题列表
     */
    List<ExamQuestion> findAllBySubject(@Param("subjectId") Long subjectId);

    /**
     * 查询真题分类统计信息
     * 返回科目+分类的二维统计数据，按题目数量降序排列
     * 
     * @param subjectId 科目ID筛选（可选，为null时统计所有科目）
     * @return 分类统计列表
     */
    List<ExamCategoryStatVO> findCategoryStats(@Param("subjectId") Long subjectId);
}
