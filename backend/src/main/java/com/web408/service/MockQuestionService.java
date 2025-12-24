package com.web408.service;

import com.web408.pojo.dto.MockQuestionCreateDTO;
import com.web408.pojo.dto.MockQuestionUpdateDTO;
import com.web408.pojo.entity.MockQuestion;
import com.web408.pojo.vo.CategoryStatVO;
import com.web408.pojo.vo.PageVO;

import java.util.List;
import java.util.Map;

/**
 * 模拟题服务接口
 */
public interface MockQuestionService {
    
    /**
     * 创建模拟题（自动获取当前用户）
     * 遵循KISS原则：Service层统一处理用户认证和DTO转换逻辑
     * 
     * @param dto 创建请求DTO
     * @return 创建成功的模拟题
     */
    MockQuestion createWithCurrentUser(MockQuestionCreateDTO dto);
    
    /**
     * 创建模拟题
     * 
     * @param mockQuestion 模拟题对象
     * @return 创建成功的模拟题
     */
    MockQuestion create(MockQuestion mockQuestion);
    
    /**
     * 根据ID查询模拟题
     * 
     * @param id 模拟题ID
     * @return 模拟题对象
     */
    MockQuestion findById(Long id);
    
    /**
     * 更新模拟题（使用DTO）
     * 遵循KISS原则：Service层统一处理DTO转换逻辑
     * 
     * @param id 模拟题ID
     * @param dto 更新请求DTO
     * @return 更新后的模拟题
     */
    MockQuestion updateByDTO(Long id, MockQuestionUpdateDTO dto);
    
    /**
     * 更新模拟题
     * 
     * @param mockQuestion 模拟题对象
     * @return 更新后的模拟题
     */
    MockQuestion update(MockQuestion mockQuestion);
    
    /**
     * 删除模拟题
     * 
     * @param id 模拟题ID
     * @return 是否删除成功
     */
    boolean delete(Long id);
    
    /**
     * 分页查询模拟题
     * 
     * @param page 页码
     * @param size 每页大小
     * @param source 来源机构（可选）
     * @param category 分类（可选）
     * @param subjectId 科目ID（可选）
     * @param noCategory 是否筛选无分类的题目（可选）
     * @param keyword 搜索关键词（可选，匹配title或content）
     * @param sortField 排序字段（可选）
     * @param sortOrder 排序方向（可选）
     * @return 分页结果
     */
    PageVO<MockQuestion> findByPage(int page, int size, String source, String category, 
                                     Long subjectId, Boolean noCategory, String keyword,
                                     String sortField, String sortOrder);
    
    /**
     * 根据来源查询模拟题
     * 
     * @param source 来源机构
     * @param category 分类（可选）
     * @param subjectId 科目ID（可选）
     * @return 模拟题列表
     */
    List<MockQuestion> findBySource(String source, String category, Long subjectId);
    
    /**
     * 根据分类查询模拟题
     * 
     * @param category 分类
     * @return 模拟题列表
     */
    List<MockQuestion> findByCategory(String category);
    
    /**
     * 根据科目ID查询分类列表
     * 
     * @param subjectId 科目ID
     * @return 分类列表
     */
    List<String> findCategoriesBySubject(Long subjectId);

    /**
     * 根据科目ID查询分类列表（带题目数量统计）
     * 
     * @param subjectId 科目ID
     * @return 分类统计列表
     */
    List<CategoryStatVO> findCategoryStatsBySubject(Long subjectId);
    
    /**
     * 查询来源统计
     * 
     * @param category 分类（可选）
     * @return 来源统计列表
     */
    List<Map<String, Object>> getSourceStats(String category);
    
    /**
     * 查询所有来源机构列表
     * 
     * @return 来源机构列表
     */
    List<String> getAllSources();

    /**
     * 按科目统计模拟题数量
     * 
     * @return 科目ID和数量的Map列表
     */
    List<Map<String, Object>> countBySubject();

    /**
     * 根据来源获取所有不重复的标题列表
     * 用于编辑模拟题时的标题下拉选项
     * 
     * @param source 来源机构
     * @return 标题列表
     */
    List<String> getTitlesBySource(String source);
}
