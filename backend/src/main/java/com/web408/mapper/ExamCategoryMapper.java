package com.web408.mapper;

import com.web408.pojo.entity.ExamCategory;
import com.web408.pojo.vo.ExamCategoryVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 分类标签Mapper接口
 * 用途：分类标签数据访问
 * 遵循SOLID原则：单一职责，只处理分类标签数据访问
 */
@Mapper
public interface ExamCategoryMapper {

    /**
     * 查询所有分类（包含科目名称和引用统计）
     * 
     * @param questionType 题目类型：exam=真题, mock=模拟题, 为null时统计真题
     */
    List<ExamCategoryVO> findAll(@Param("questionType") String questionType);

    /**
     * 按科目查询所有分类（包含科目名称和引用统计）
     * 
     * @param subjectId    科目ID
     * @param questionType 题目类型：exam=真题, mock=模拟题, 为null时统计真题
     */
    List<ExamCategoryVO> findBySubjectId(@Param("subjectId") Long subjectId,
            @Param("questionType") String questionType);

    /**
     * 按科目查询启用的分类（用于前端选择器）
     */
    List<ExamCategoryVO> findEnabledBySubjectId(@Param("subjectId") Long subjectId);

    /**
     * 按科目查询顶级分类（parent_id IS NULL）
     */
    List<ExamCategoryVO> findRootCategoriesBySubjectId(@Param("subjectId") Long subjectId);

    /**
     * 按科目查询二级分类（parent_id不为空且其父分类是顶级分类）
     * 用于三级分类支持：二级分类也可作为父分类
     */
    List<ExamCategoryVO> findSecondLevelCategoriesBySubjectId(@Param("subjectId") Long subjectId);

    /**
     * 查询指定父分类下的子分类
     */
    List<ExamCategoryVO> findByParentId(@Param("parentId") Long parentId);

    /**
     * 查询指定父分类下的启用子分类
     */
    List<ExamCategoryVO> findEnabledByParentId(@Param("parentId") Long parentId);

    /**
     * 检查分类是否有子分类
     */
    int countByParentId(@Param("parentId") Long parentId);

    /**
     * 根据ID查询分类
     */
    ExamCategory findById(@Param("id") Long id);

    /**
     * 根据科目和名称查询分类
     */
    ExamCategory findBySubjectAndName(@Param("subjectId") Long subjectId, @Param("name") String name);

    /**
     * 根据科目和编码查询分类
     */
    ExamCategory findBySubjectAndCode(@Param("subjectId") Long subjectId, @Param("code") String code);

    /**
     * 检查名称是否存在（排除指定ID）
     */
    int existsByName(@Param("subjectId") Long subjectId, @Param("name") String name,
            @Param("excludeId") Long excludeId);

    /**
     * 检查编码是否存在（排除指定ID）
     */
    int existsByCode(@Param("subjectId") Long subjectId, @Param("code") String code,
            @Param("excludeId") Long excludeId);

    /**
     * 插入分类
     */
    int insert(ExamCategory category);

    /**
     * 更新分类
     */
    int update(ExamCategory category);

    /**
     * 删除分类
     */
    int deleteById(@Param("id") Long id);

    /**
     * 统计分类被引用的题目数量（真题）
     */
    int countExamQuestionsByCategory(@Param("subjectId") Long subjectId, @Param("categoryName") String categoryName);

    /**
     * 统计分类被引用的题目数量（模拟题）
     */
    int countMockQuestionsByCategory(@Param("subjectId") Long subjectId, @Param("categoryName") String categoryName);

    /**
     * 统计去重后的题目总数（按科目）
     * 用于解决一道题目有多个标签时的重复计数问题
     * 
     * @param subjectId    科目ID
     * @param questionType 题目类型：exam=真题, mock=模拟题
     */
    int countDistinctQuestionsBySubject(@Param("subjectId") Long subjectId, @Param("questionType") String questionType);

    /**
     * 统计去重后的题目总数（全局）
     * 用于解决一道题目有多个标签时的重复计数问题
     * 
     * @param questionType 题目类型：exam=真题, mock=模拟题
     */
    int countDistinctQuestionsTotal(@Param("questionType") String questionType);

    /**
     * 批量更新真题表中的分类名称
     * 当分类名称变更时，同步更新所有引用该分类的题目
     * 
     * @param subjectId 科目ID
     * @param oldName   旧分类名称
     * @param newName   新分类名称
     * @return 更新的记录数
     */
    int updateExamQuestionCategoryName(@Param("subjectId") Long subjectId,
            @Param("oldName") String oldName,
            @Param("newName") String newName);

    /**
     * 批量更新模拟题表中的分类名称
     * 
     * @param subjectId 科目ID
     * @param oldName   旧分类名称
     * @param newName   新分类名称
     * @return 更新的记录数
     */
    int updateMockQuestionCategoryName(@Param("subjectId") Long subjectId,
            @Param("oldName") String oldName,
            @Param("newName") String newName);
}
