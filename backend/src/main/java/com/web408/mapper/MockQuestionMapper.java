package com.web408.mapper;

import com.web408.pojo.entity.MockQuestion;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.web408.pojo.vo.CategoryStatVO;

import java.util.List;
import java.util.Map;

/**
 * 模拟题Mapper接口
 */
@Mapper
public interface MockQuestionMapper {
    
    /**
     * 插入模拟题
     * 
     * @param mockQuestion 模拟题对象
     * @return 影响行数
     */
    int insert(MockQuestion mockQuestion);

    /**
     * 根据ID查询模拟题
     * 
     * @param id 模拟题ID
     * @return MockQuestion对象，不存在返回null
     */
    MockQuestion findById(@Param("id") Long id);

    /**
     * 根据来源和题号查询模拟题（用于唯一性校验）
     * 
     * @param source 来源机构
     * @param questionNumber 题号
     * @return MockQuestion对象，不存在返回null
     */
    MockQuestion findBySourceAndNumber(@Param("source") String source, 
                                       @Param("questionNumber") Integer questionNumber);

    /**
     * 根据来源、标题和题号查询模拟题（用于唯一性校验）
     * 唯一性约束：source + title + question_number 组合唯一
     * 
     * @param source 来源机构
     * @param title 题目标题
     * @param questionNumber 题号
     * @return MockQuestion对象，不存在返回null
     */
    MockQuestion findBySourceTitleAndNumber(@Param("source") String source,
                                            @Param("title") String title,
                                            @Param("questionNumber") Integer questionNumber);

    /**
     * 查询所有模拟题
     * 
     * @return 模拟题列表
     */
    List<MockQuestion> findAll();

    /**
     * 根据来源查询模拟题
     * 
     * @param source 来源机构
     * @param category 分类（可选）
     * @param subjectId 科目ID（可选）
     * @return 模拟题列表
     */
    List<MockQuestion> findBySource(@Param("source") String source,
                                    @Param("category") String category,
                                    @Param("subjectId") Long subjectId);

    /**
     * 根据分类查询模拟题
     * 
     * @param category 分类
     * @return 模拟题列表
     */
    List<MockQuestion> findByCategory(@Param("category") String category);

    /**
     * 更新模拟题
     * 
     * @param mockQuestion 模拟题对象
     * @return 影响行数
     */
    int update(MockQuestion mockQuestion);

    /**
     * 删除模拟题
     * 
     * @param id 模拟题ID
     * @return 影响行数
     */
    int deleteById(@Param("id") Long id);
    
    /**
     * 分页查询模拟题（支持来源、分类、关键词筛选和排序）
     * 
     * @param offset 偏移量
     * @param limit 每页大小
     * @param source 来源机构（可选）
     * @param category 分类（可选）
     * @param subjectId 科目ID（可选）
     * @param noCategory 是否筛选无分类的题目（可选）
     * @param keyword 搜索关键词（可选，匹配title或content）
     * @param sortField 排序字段（可选）
     * @param sortOrder 排序方向（可选）
     * @return 模拟题列表
     */
    List<MockQuestion> findByPage(@Param("offset") int offset, 
                                  @Param("limit") int limit, 
                                  @Param("source") String source,
                                  @Param("category") String category,
                                  @Param("subjectId") Long subjectId,
                                  @Param("noCategory") Boolean noCategory,
                                  @Param("keyword") String keyword,
                                  @Param("sortField") String sortField,
                                  @Param("sortOrder") String sortOrder);
    
    /**
     * 统计模拟题总数（支持来源、分类、科目、关键词筛选）
     * 
     * @param source 来源机构（可选）
     * @param category 分类（可选）
     * @param subjectId 科目ID（可选）
     * @param noCategory 是否筛选无分类的题目（可选）
     * @param keyword 搜索关键词（可选，匹配title或content）
     * @return 总记录数
     */
    long count(@Param("source") String source,
               @Param("category") String category,
               @Param("subjectId") Long subjectId,
               @Param("noCategory") Boolean noCategory,
               @Param("keyword") String keyword);

    /**
     * 根据科目ID查询该科目下实际存在模拟题的分类列表
     *
     * @param subjectId 科目ID
     * @return 分类名称列表（去重且不包含空分类）
     */
    List<String> findCategoriesBySubject(@Param("subjectId") Long subjectId);

    /**
     * 根据科目ID查询该科目下实际存在模拟题的分类列表（带题目数量统计）
     *
     * @param subjectId 科目ID
     * @return 分类统计列表（包含分类名称和题目数量）
     */
    List<CategoryStatVO> findCategoryStatsBySubject(@Param("subjectId") Long subjectId);

    /**
     * 查询来源统计（按来源机构分组统计题目数量）
     * 
     * @param category 分类（可选）
     * @return 来源统计列表
     */
    List<Map<String, Object>> findSourceStats(@Param("category") String category);

    /**
     * 查询所有不重复的来源机构列表
     * 
     * @return 来源机构列表
     */
    List<String> findAllSources();

    /**
     * 按科目统计模拟题数量
     * 
     * @return 科目ID和数量的Map列表
     */
    List<Map<String, Object>> countBySubject();

    /**
     * 根据来源查询所有不重复的标题列表
     * 用于编辑模拟题时的标题下拉选项
     * 
     * @param source 来源机构
     * @return 标题列表（去重且不包含空标题）
     */
    List<String> findTitlesBySource(@Param("source") String source);
}
