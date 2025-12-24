package com.web408.service.impl;

import com.web408.mapper.MockQuestionMapper;
import com.web408.mapper.UserMapper;
import com.web408.pojo.dto.MockQuestionCreateDTO;
import com.web408.pojo.dto.MockQuestionUpdateDTO;
import com.web408.pojo.entity.MockQuestion;
import com.web408.pojo.entity.User;
import com.web408.pojo.vo.CategoryStatVO;
import com.web408.pojo.vo.PageVO;
import com.web408.service.MockQuestionService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/**
 * 模拟题服务实现类
 * 遵循KISS原则：简单直接的CRUD操作
 */
@Service
public class MockQuestionServiceImpl implements MockQuestionService {
    
    @Autowired
    private MockQuestionMapper mockQuestionMapper;
    
    @Autowired
    private UserMapper userMapper;
    
    /**
     * 创建模拟题（自动获取当前用户）
     * 遵循KISS原则：Service层统一处理用户认证和DTO转换逻辑
     */
    @Override
    public MockQuestion createWithCurrentUser(MockQuestionCreateDTO dto) {
        // 从SecurityContext获取当前用户
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String username = authentication.getName();
        User user = userMapper.findByUsername(username);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        
        // DTO转Entity
        MockQuestion mockQuestion = new MockQuestion();
        BeanUtils.copyProperties(dto, mockQuestion);
        mockQuestion.setAuthorId(user.getId());
        
        return create(mockQuestion);
    }
    
    /**
     * 更新模拟题（使用DTO）
     * 遵循KISS原则：Service层统一处理DTO转换逻辑
     */
    @Override
    public MockQuestion updateByDTO(Long id, MockQuestionUpdateDTO dto) {
        MockQuestion existing = findById(id);
        if (existing == null) {
            throw new RuntimeException("模拟题不存在");
        }
        
        // DTO转Entity
        MockQuestion mockQuestion = new MockQuestion();
        BeanUtils.copyProperties(dto, mockQuestion);
        mockQuestion.setId(id);
        
        return update(mockQuestion);
    }
    
    @Override
    public MockQuestion create(MockQuestion mockQuestion) {
        // 唯一性校验：source + title + question_number 组合唯一
        checkDuplicateMockQuestion(mockQuestion, null);
        mockQuestionMapper.insert(mockQuestion);
        return mockQuestion;
    }
    
    /**
     * 检查模拟题是否重复（source + title + question_number 组合唯一）
     * 
     * @param mockQuestion 待检查的模拟题
     * @param excludeId 排除的ID（更新时排除自身）
     */
    private void checkDuplicateMockQuestion(MockQuestion mockQuestion, Long excludeId) {
        MockQuestion existing = mockQuestionMapper.findBySourceTitleAndNumber(
            mockQuestion.getSource(),
            mockQuestion.getTitle(),
            mockQuestion.getQuestionNumber()
        );
        if (existing != null && (excludeId == null || !existing.getId().equals(excludeId))) {
            throw new RuntimeException("模拟题已存在：相同来源、标题和题号的题目已录入");
        }
    }
    
    @Override
    public MockQuestion findById(Long id) {
        return mockQuestionMapper.findById(id);
    }
    
    @Override
    public MockQuestion update(MockQuestion mockQuestion) {
        // 唯一性校验：source + title + question_number 组合唯一（排除自身）
        checkDuplicateMockQuestion(mockQuestion, mockQuestion.getId());
        mockQuestionMapper.update(mockQuestion);
        return mockQuestionMapper.findById(mockQuestion.getId());
    }
    
    @Override
    public boolean delete(Long id) {
        return mockQuestionMapper.deleteById(id) > 0;
    }
    
    @Override
    public PageVO<MockQuestion> findByPage(int page, int size, String source, String category, 
                                            Long subjectId, Boolean noCategory, String keyword,
                                            String sortField, String sortOrder) {
        int offset = (page - 1) * size;
        // 处理关键词空字符串为null
        if (keyword != null && keyword.trim().isEmpty()) {
            keyword = null;
        }
        List<MockQuestion> list = mockQuestionMapper.findByPage(offset, size, source, category, 
                                                                 subjectId, noCategory, keyword, sortField, sortOrder);
        long total = mockQuestionMapper.count(source, category, subjectId, noCategory, keyword);
        return new PageVO<>(list, total, page, size);
    }
    
    @Override
    public List<MockQuestion> findBySource(String source, String category, Long subjectId) {
        return mockQuestionMapper.findBySource(source, category, subjectId);
    }
    
    @Override
    public List<MockQuestion> findByCategory(String category) {
        return mockQuestionMapper.findByCategory(category);
    }
    
    @Override
    public List<String> findCategoriesBySubject(Long subjectId) {
        return mockQuestionMapper.findCategoriesBySubject(subjectId);
    }

    @Override
    public List<CategoryStatVO> findCategoryStatsBySubject(Long subjectId) {
        return mockQuestionMapper.findCategoryStatsBySubject(subjectId);
    }
    
    @Override
    public List<Map<String, Object>> getSourceStats(String category) {
        return mockQuestionMapper.findSourceStats(category);
    }
    
    @Override
    public List<String> getAllSources() {
        return mockQuestionMapper.findAllSources();
    }

    @Override
    public List<Map<String, Object>> countBySubject() {
        return mockQuestionMapper.countBySubject();
    }

    @Override
    public List<String> getTitlesBySource(String source) {
        // 来源为空时返回空列表
        if (source == null || source.trim().isEmpty()) {
            return java.util.Collections.emptyList();
        }
        return mockQuestionMapper.findTitlesBySource(source);
    }
}
