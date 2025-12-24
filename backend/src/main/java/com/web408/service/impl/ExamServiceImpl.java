package com.web408.service.impl;

import com.web408.mapper.ExamQuestionMapper;
import com.web408.mapper.UserMapper;
import com.web408.pojo.dto.ExamQuestionCreateDTO;
import com.web408.pojo.dto.ExamQuestionUpdateDTO;
import com.web408.pojo.entity.ExamQuestion;
import com.web408.pojo.entity.User;
import com.web408.pojo.vo.ExamCategoryStatVO;
import com.web408.pojo.vo.ExamYearStatVO;
import com.web408.pojo.vo.ExportResultVO;
import com.web408.pojo.vo.PageVO;
import com.web408.service.ExamService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 真题服务实现类
 * 遵循KISS原则：业务逻辑清晰简单
 * 遵循单一职责原则：只处理真题相关业务
 */
@Service
public class ExamServiceImpl implements ExamService {

    @Autowired
    private ExamQuestionMapper examQuestionMapper;
    
    @Autowired
    private UserMapper userMapper;

    @Override
    public List<ExamQuestion> findAll() {
        return examQuestionMapper.findAll();
    }

    /**
     * 分页查询真题
     * 1. 参数校验
     * 2. 计算偏移量
     * 3. 处理空字符串为null
     * 4. 查询数据列表
     * 5. 查询总记录数
     * 6. 封装分页响应
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
    @Override
    public PageVO<ExamQuestion> findByPage(int page, int size, Integer year, String category, Long subjectId, Boolean noCategory, String keyword, String sortField, String sortOrder) {
        // 参数校验：页码最小为1
        if (page < 1) {
            page = 1;
        }
        // 参数校验：每页大小在1-100之间
        if (size < 1) {
            size = 10;
        }
        if (size > 100) {
            size = 100;
        }

        // 计算偏移量：offset = (page - 1) * size
        int offset = (page - 1) * size;

        // 处理空字符串为null
        if (category != null && category.trim().isEmpty()) {
            category = null;
        }
        // 处理关键词空字符串为null
        if (keyword != null && keyword.trim().isEmpty()) {
            keyword = null;
        }
        if (sortField != null && sortField.trim().isEmpty()) {
            sortField = null;
        }
        if (sortOrder != null && sortOrder.trim().isEmpty()) {
            sortOrder = null;
        }

        // 查询数据列表（新增keyword参数）
        List<ExamQuestion> dataList = examQuestionMapper.findByPage(offset, size, year, category, subjectId, noCategory, keyword, sortField, sortOrder);

        // 查询总记录数（新增keyword参数）
        long total = examQuestionMapper.count(year, category, subjectId, noCategory, keyword);

        // 封装分页响应
        return new PageVO<>(dataList, total, page, size);
    }

    /**
     * 根据ID查询真题详情
     * 
     * @param id 真题ID
     * @return ExamQuestion对象，不存在返回null
     */
    @Override
    public ExamQuestion findById(Long id) {
        return examQuestionMapper.findById(id);
    }

    /**
     * 检查指定年份和题号的真题是否已存在
     * 
     * @param year 年份
     * @param questionNumber 题号
     * @return ExamQuestion对象，不存在返回null
     */
    @Override
    public ExamQuestion checkDuplicate(Integer year, Integer questionNumber) {
        if (year == null || questionNumber == null) {
            return null;
        }
        return examQuestionMapper.findByYearAndNumber(year, questionNumber);
    }

    /**
     * 创建真题（自动获取当前用户）
     * 遵循KISS原则：Service层统一处理用户认证逻辑
     * 
     * @param request 创建请求DTO
     * @return 创建后的真题对象
     */
    @Override
    public ExamQuestion createWithCurrentUser(ExamQuestionCreateDTO request) {
        // 从SecurityContext获取当前用户
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String username = authentication.getName();
        User user = userMapper.findByUsername(username);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        return create(request, user.getId());
    }
    
    /**
     * 创建真题
     * 遵循KISS原则：简单直接的创建逻辑
     * 
     * @param request 创建请求DTO
     * @param authorId 作者ID
     * @return 创建后的真题对象
     */
    @Override
    public ExamQuestion create(ExamQuestionCreateDTO request, Long authorId) {
        // 校验题号唯一性（仅当题号不为空时）
        if (request.getQuestionNumber() != null) {
            ExamQuestion duplicate = examQuestionMapper.findByYearAndNumber(
                request.getYear(), 
                request.getQuestionNumber()
            );
            if (duplicate != null) {
                throw new RuntimeException(
                    String.format("年份 %d 的题号 %d 已存在，请使用其他题号", 
                        request.getYear(), 
                        request.getQuestionNumber())
                );
            }
        }
        
        // 构建ExamQuestion对象
        ExamQuestion examQuestion = new ExamQuestion();
        examQuestion.setYear(request.getYear());
        examQuestion.setQuestionNumber(request.getQuestionNumber());
        examQuestion.setQuestionType(request.getQuestionType());
        examQuestion.setTitle(request.getTitle());
        examQuestion.setContent(request.getContent());
        examQuestion.setOptions(request.getOptions());
        examQuestion.setAnswer(request.getAnswer());
        examQuestion.setSubjectId(request.getSubjectId());
        examQuestion.setCategory(request.getCategory());
        examQuestion.setDifficulty(request.getDifficulty());
        examQuestion.setAuthorId(authorId);
        examQuestion.setCreateTime(LocalDateTime.now());
        examQuestion.setUpdateTime(LocalDateTime.now());

        // 插入数据库
        examQuestionMapper.insert(examQuestion);

        return examQuestion;
    }

    /**
     * 更新真题
     * 遵循KISS原则：简单直接的更新逻辑
     * 
     * @param request 更新请求DTO
     * @return 更新后的真题对象
     */
    @Override
    public ExamQuestion update(ExamQuestionUpdateDTO request) {
        // 检查真题是否存在
        ExamQuestion existing = examQuestionMapper.findById(request.getId());
        if (existing == null) {
            throw new RuntimeException("真题不存在");
        }

        // 校验题号唯一性（仅当题号不为空且发生变化时）
        if (request.getQuestionNumber() != null) {
            // 检查是否修改了年份或题号
            boolean yearChanged = !request.getYear().equals(existing.getYear());
            boolean numberChanged = !request.getQuestionNumber().equals(existing.getQuestionNumber());
            
            if (yearChanged || numberChanged) {
                ExamQuestion duplicate = examQuestionMapper.findByYearAndNumber(
                    request.getYear(), 
                    request.getQuestionNumber()
                );
                // 如果找到重复且不是当前记录本身
                if (duplicate != null && !duplicate.getId().equals(request.getId())) {
                    throw new RuntimeException(
                        String.format("年份 %d 的题号 %d 已存在，请使用其他题号", 
                            request.getYear(), 
                            request.getQuestionNumber())
                    );
                }
            }
        }
        
        // 更新字段
        existing.setYear(request.getYear());
        existing.setQuestionNumber(request.getQuestionNumber());
        existing.setQuestionType(request.getQuestionType());
        existing.setTitle(request.getTitle());
        existing.setContent(request.getContent());
        existing.setOptions(request.getOptions());
        existing.setAnswer(request.getAnswer());
        existing.setSubjectId(request.getSubjectId());
        existing.setCategory(request.getCategory());
        existing.setDifficulty(request.getDifficulty());
        existing.setUpdateTime(LocalDateTime.now());

        // 更新数据库
        int rows = examQuestionMapper.update(existing);
        if (rows == 0) {
            throw new RuntimeException("更新失败");
        }

        return existing;
    }

    /**
     * 删除真题
     * 遵循KISS原则：简单直接的删除逻辑
     * 
     * @param id 真题ID
     * @return 是否删除成功
     */
    @Override
    public boolean delete(Long id) {
        // 检查真题是否存在
        ExamQuestion existing = examQuestionMapper.findById(id);
        if (existing == null) {
            throw new RuntimeException("真题不存在");
        }

        // 删除真题
        int rows = examQuestionMapper.deleteById(id);
        return rows > 0;
    }

    /**
     * 根据年份查询所有真题（按题号排序）
     * 用于年份页面展示：一次性加载指定年份的所有题目
     * 遵循KISS原则：直接调用Mapper查询，无复杂业务逻辑
     *
     * @param year 年份
     * @param category 分类（可选）
     * @param subjectId 科目ID（可选）
     * @return 真题列表，按题号升序排列
     */
    @Override
    public List<ExamQuestion> findByYear(Integer year, String category, Long subjectId) {
        if (category != null && category.trim().isEmpty()) {
            category = null;
        }
        return examQuestionMapper.findByYear(year, category, subjectId);
    }

    /**
     * 根据科目ID查询该科目下实际存在真题的分类名称列表
     * 由后端统一聚合，前端仅负责展示
     *
     * @param subjectId 科目ID
     * @return 分类名称列表（去重且不包含空分类）
     */
    @Override
    public List<String> getCategoriesBySubject(Long subjectId) {
        if (subjectId == null) {
            return new ArrayList<>();
        }
        return examQuestionMapper.findCategoriesBySubject(subjectId);
    }

    @Override
    public List<ExamYearStatVO> getYearStats(String category) {
        if (category != null && category.trim().isEmpty()) {
            category = null;
        }
        return examQuestionMapper.findYearStats(category);
    }

    @Override
    public List<ExamQuestion> findAllForIndex(String category) {
        if (category != null && category.trim().isEmpty()) {
            category = null;
        }
        return examQuestionMapper.findAllForIndex(category);
    }

    /**
     * 按科目导出真题
     * 遵循KISS原则：Service层处理所有导出逻辑，包括格式转换
     * 
     * @param subjectId 科目ID
     * @param format 导出格式（markdown）
     * @return 导出结果VO，包含文件字节、文件名和内容类型
     */
    @Override
    public ExportResultVO exportBySubject(Long subjectId, String format) {
        if (subjectId == null) {
            throw new RuntimeException("科目ID不能为空");
        }
        if (format == null || format.trim().isEmpty()) {
            throw new RuntimeException("导出格式不能为空");
        }
        
        List<ExamQuestion> exams = examQuestionMapper.findAllBySubject(subjectId);
        
        // 根据格式生成文件内容
        if ("markdown".equalsIgnoreCase(format)) {
            return generateMarkdownExport(exams);
        } else {
            throw new RuntimeException("不支持的导出格式：" + format);
        }
    }
    
    /**
     * 生成Markdown格式的导出文件
     * 
     * @param exams 真题列表
     * @return 导出结果VO
     */
    private ExportResultVO generateMarkdownExport(List<ExamQuestion> exams) {
        StringBuilder sb = new StringBuilder();
        sb.append("# 真题导出\n\n");
        
        for (ExamQuestion exam : exams) {
            sb.append("## ").append(exam.getYear()).append("年 第")
              .append(exam.getQuestionNumber()).append("题\n\n");
            sb.append(exam.getContent()).append("\n\n");
            if (exam.getAnswer() != null) {
                sb.append("**答案：**\n").append(exam.getAnswer()).append("\n\n");
            }
            sb.append("---\n\n");
        }
        
        byte[] content = sb.toString().getBytes(StandardCharsets.UTF_8);
        return new ExportResultVO(content, "真题导出.md", "text/plain; charset=UTF-8");
    }

    /**
     * 查询真题分类统计信息
     * 遵循KISS原则：简单直接地调用Mapper查询
     * 
     * @param subjectId 科目ID筛选（可选）
     * @return 分类统计列表（按题目数量降序）
     */
    @Override
    public List<ExamCategoryStatVO> getCategoryStats(Long subjectId) {
        return examQuestionMapper.findCategoryStats(subjectId);
    }

    @Override
    public List<ExamQuestion> findBySubjectAndCategory(Long subjectId, String category) {
        if (category == null || category.trim().isEmpty()) {
            return new ArrayList<>();
        }
        return examQuestionMapper.findBySubjectAndCategory(subjectId, category);
    }
}
