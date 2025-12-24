package com.web408.service.impl;

import com.web408.mapper.ExamCategoryMapper;
import com.web408.mapper.SubjectMapper;
import com.web408.pojo.dto.ExamCategoryDTO;
import com.web408.pojo.entity.ExamCategory;
import com.web408.pojo.entity.Subject;
import com.web408.pojo.vo.ExamCategoryVO;
import com.web408.service.ExamCategoryService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 分类标签服务实现类
 * 用途：实现分类标签管理的业务逻辑
 * 遵循KISS原则：简单直接的业务实现
 */
@Service
public class ExamCategoryServiceImpl implements ExamCategoryService {

    @Autowired
    private ExamCategoryMapper examCategoryMapper;

    @Autowired
    private SubjectMapper subjectMapper;

    @Override
    public List<ExamCategoryVO> getAllCategories(String questionType) {
        // 默认统计真题
        String type = (questionType == null || questionType.isEmpty()) ? "exam" : questionType;
        return examCategoryMapper.findAll(type);
    }

    @Override
    public List<ExamCategoryVO> getCategoriesBySubject(Long subjectId, String questionType) {
        if (subjectId == null) {
            throw new RuntimeException("科目ID不能为空");
        }
        // 默认统计真题
        String type = (questionType == null || questionType.isEmpty()) ? "exam" : questionType;
        return examCategoryMapper.findBySubjectId(subjectId, type);
    }

    @Override
    public List<ExamCategoryVO> getEnabledCategoriesBySubject(Long subjectId) {
        if (subjectId == null) {
            throw new RuntimeException("科目ID不能为空");
        }
        return examCategoryMapper.findEnabledBySubjectId(subjectId);
    }

    @Override
    public List<ExamCategoryVO> getCategoryTreeBySubject(Long subjectId) {
        if (subjectId == null) {
            throw new RuntimeException("科目ID不能为空");
        }
        // 获取顶级分类
        List<ExamCategoryVO> rootCategories = examCategoryMapper.findRootCategoriesBySubjectId(subjectId);
        // 递归构建完整的树形结构（支持三级及以上）
        for (ExamCategoryVO root : rootCategories) {
            buildChildrenFromDb(root);
        }
        return rootCategories;
    }

    /**
     * 从数据库递归构建子分类树
     * 用于获取所有分类（包括禁用的）
     * 
     * @param parent 父分类
     */
    private void buildChildrenFromDb(ExamCategoryVO parent) {
        List<ExamCategoryVO> children = examCategoryMapper.findByParentId(parent.getId());
        if (!children.isEmpty()) {
            // 递归为每个子分类构建其子分类
            for (ExamCategoryVO child : children) {
                buildChildrenFromDb(child);
            }
            parent.setChildren(children);
        } else {
            parent.setChildren(null);
        }
    }

    @Override
    public List<ExamCategoryVO> getEnabledCategoryTreeBySubject(Long subjectId) {
        if (subjectId == null) {
            throw new RuntimeException("科目ID不能为空");
        }
        // 获取所有启用的分类
        List<ExamCategoryVO> allEnabled = examCategoryMapper.findEnabledBySubjectId(subjectId);
        // 筛选顶级分类
        List<ExamCategoryVO> rootCategories = allEnabled.stream()
                .filter(c -> c.getParentId() == null)
                .collect(Collectors.toList());
        // 递归构建完整的树形结构（支持三级及以上）
        for (ExamCategoryVO root : rootCategories) {
            buildChildrenRecursively(root, allEnabled);
        }
        return rootCategories;
    }

    /**
     * 递归构建子分类树
     * 支持任意层级的分类结构
     * 
     * @param parent        父分类
     * @param allCategories 所有分类列表
     */
    private void buildChildrenRecursively(ExamCategoryVO parent, List<ExamCategoryVO> allCategories) {
        List<ExamCategoryVO> children = allCategories.stream()
                .filter(c -> parent.getId().equals(c.getParentId()))
                .collect(Collectors.toList());
        if (!children.isEmpty()) {
            // 递归为每个子分类构建其子分类
            for (ExamCategoryVO child : children) {
                buildChildrenRecursively(child, allCategories);
            }
            parent.setChildren(children);
        } else {
            parent.setChildren(null);
        }
    }

    @Override
    public List<ExamCategoryVO> getEnabledCategoryTreeWithStatsBySubject(Long subjectId, String questionType) {
        if (subjectId == null) {
            throw new RuntimeException("科目ID不能为空");
        }
        // 默认为真题
        String type = (questionType == null || questionType.isEmpty()) ? "exam" : questionType;

        // 获取所有启用的分类
        List<ExamCategoryVO> allEnabled = examCategoryMapper.findEnabledBySubjectId(subjectId);

        // 为每个分类填充指定题型的题目数量
        for (ExamCategoryVO category : allEnabled) {
            int count = 0;
            switch (type) {
                case "mock":
                    count = examCategoryMapper.countMockQuestionsByCategory(subjectId, category.getName());
                    break;
                default: // exam
                    count = examCategoryMapper.countExamQuestionsByCategory(subjectId, category.getName());
                    break;
            }
            category.setQuestionCount(count);
        }

        // 筛选顶级分类
        List<ExamCategoryVO> rootCategories = allEnabled.stream()
                .filter(c -> c.getParentId() == null)
                .collect(Collectors.toList());

        // 递归构建完整的树形结构
        for (ExamCategoryVO root : rootCategories) {
            buildChildrenRecursively(root, allEnabled);
        }

        // 过滤掉题目数为0的分类（包括递归计算子分类后仍然为0的父分类）
        return filterEmptyCategories(rootCategories);
    }

    /**
     * 递归过滤题目数为0的分类
     * 规则：
     * 1. 叶子节点（无子分类）：直接根据 questionCount 判断
     * 2. 父节点：如果自身有题目或者有至少一个非空子分类，则保留
     * 
     * @param categories 分类列表
     * @return 过滤后的分类列表
     */
    private List<ExamCategoryVO> filterEmptyCategories(List<ExamCategoryVO> categories) {
        if (categories == null || categories.isEmpty()) {
            return categories;
        }

        List<ExamCategoryVO> result = new java.util.ArrayList<>();
        for (ExamCategoryVO category : categories) {
            // 先递归处理子分类
            if (category.getChildren() != null && !category.getChildren().isEmpty()) {
                List<ExamCategoryVO> filteredChildren = filterEmptyCategories(category.getChildren());
                category.setChildren(filteredChildren.isEmpty() ? null : filteredChildren);
            }

            // 判断是否保留该分类
            int selfCount = category.getQuestionCount() != null ? category.getQuestionCount() : 0;
            boolean hasNonEmptyChildren = category.getChildren() != null && !category.getChildren().isEmpty();

            // 如果自身有题目或者有非空子分类，则保留
            if (selfCount > 0 || hasNonEmptyChildren) {
                result.add(category);
            }
        }
        return result;
    }

    @Override
    public List<ExamCategoryVO> getAvailableParentCategories(Long subjectId, Long excludeId) {
        if (subjectId == null) {
            throw new RuntimeException("科目ID不能为空");
        }
        // 三级分类支持：顶级分类和二级分类都可作为父分类
        // 获取顶级分类
        List<ExamCategoryVO> rootCategories = examCategoryMapper.findRootCategoriesBySubjectId(subjectId);
        // 获取二级分类（parentId不为空且其父分类是顶级分类）
        List<ExamCategoryVO> secondLevelCategories = examCategoryMapper.findSecondLevelCategoriesBySubjectId(subjectId);

        // 合并顶级和二级分类
        List<ExamCategoryVO> availableParents = new java.util.ArrayList<>(rootCategories);
        availableParents.addAll(secondLevelCategories);

        // 排除自身及其子分类（编辑时）
        if (excludeId != null) {
            // 获取要排除的分类及其所有子孙分类ID
            java.util.Set<Long> excludeIds = getDescendantIds(excludeId);
            excludeIds.add(excludeId);
            availableParents = availableParents.stream()
                    .filter(c -> !excludeIds.contains(c.getId()))
                    .collect(Collectors.toList());
        }
        return availableParents;
    }

    /**
     * 获取分类的所有子孙分类ID（递归）
     */
    private java.util.Set<Long> getDescendantIds(Long parentId) {
        java.util.Set<Long> ids = new java.util.HashSet<>();
        List<ExamCategoryVO> children = examCategoryMapper.findByParentId(parentId);
        for (ExamCategoryVO child : children) {
            ids.add(child.getId());
            ids.addAll(getDescendantIds(child.getId()));
        }
        return ids;
    }

    /**
     * 获取分类下子分类的最大深度（递归）
     */
    private int getMaxChildDepth(Long parentId) {
        List<ExamCategoryVO> children = examCategoryMapper.findByParentId(parentId);
        if (children.isEmpty()) {
            return 0;
        }
        int maxDepth = 0;
        for (ExamCategoryVO child : children) {
            int childDepth = 1 + getMaxChildDepth(child.getId());
            maxDepth = Math.max(maxDepth, childDepth);
        }
        return maxDepth;
    }

    @Override
    public ExamCategoryVO getCategoryById(Long id) {
        ExamCategory category = examCategoryMapper.findById(id);
        if (category == null) {
            throw new RuntimeException("分类不存在：ID=" + id);
        }
        return convertToVO(category);
    }

    @Override
    @Transactional
    public ExamCategoryVO createCategory(ExamCategoryDTO request) {
        // 检查科目是否存在
        Subject subject = subjectMapper.findById(request.getSubjectId());
        if (subject == null) {
            throw new RuntimeException("科目不存在：ID=" + request.getSubjectId());
        }

        // 检查同科目下名称是否已存在
        if (examCategoryMapper.existsByName(request.getSubjectId(), request.getName(), null) > 0) {
            throw new RuntimeException("该科目下分类名称已存在：" + request.getName());
        }

        // 检查同科目下编码是否已存在
        if (examCategoryMapper.existsByCode(request.getSubjectId(), request.getCode(), null) > 0) {
            throw new RuntimeException("该科目下分类编码已存在：" + request.getCode());
        }

        // 验证父分类（如果指定）
        if (request.getParentId() != null) {
            ExamCategory parentCategory = examCategoryMapper.findById(request.getParentId());
            if (parentCategory == null) {
                throw new RuntimeException("父分类不存在：ID=" + request.getParentId());
            }
            // 三级限制：父分类最多是二级分类（即父分类的父分类必须是顶级）
            if (parentCategory.getParentId() != null) {
                ExamCategory grandParent = examCategoryMapper.findById(parentCategory.getParentId());
                if (grandParent != null && grandParent.getParentId() != null) {
                    throw new RuntimeException("只支持三级分类，不能在第三级分类下创建子分类");
                }
            }
            // 父分类必须属于同一科目
            if (!parentCategory.getSubjectId().equals(request.getSubjectId())) {
                throw new RuntimeException("父分类必须属于同一科目");
            }
        }

        // 创建分类实体
        ExamCategory category = new ExamCategory();
        BeanUtils.copyProperties(request, category);

        // 插入数据库
        int rows = examCategoryMapper.insert(category);
        if (rows == 0) {
            throw new RuntimeException("创建分类失败");
        }

        // 返回带科目名称的VO
        ExamCategoryVO vo = convertToVO(category);
        vo.setSubjectName(subject.getName());
        return vo;
    }

    @Override
    @Transactional
    public ExamCategoryVO updateCategory(Long id, ExamCategoryDTO request) {
        // 检查分类是否存在
        ExamCategory existingCategory = examCategoryMapper.findById(id);
        if (existingCategory == null) {
            throw new RuntimeException("分类不存在：ID=" + id);
        }

        // 检查科目是否存在
        Subject subject = subjectMapper.findById(request.getSubjectId());
        if (subject == null) {
            throw new RuntimeException("科目不存在：ID=" + request.getSubjectId());
        }

        // 检查同科目下名称是否已被其他分类使用
        if (examCategoryMapper.existsByName(request.getSubjectId(), request.getName(), id) > 0) {
            throw new RuntimeException("该科目下分类名称已被其他分类使用：" + request.getName());
        }

        // 检查同科目下编码是否已被其他分类使用
        if (examCategoryMapper.existsByCode(request.getSubjectId(), request.getCode(), id) > 0) {
            throw new RuntimeException("该科目下分类编码已被其他分类使用：" + request.getCode());
        }

        // 验证父分类（如果指定）
        if (request.getParentId() != null) {
            // 不能将自己设为父分类
            if (request.getParentId().equals(id)) {
                throw new RuntimeException("不能将自己设为父分类");
            }
            ExamCategory parentCategory = examCategoryMapper.findById(request.getParentId());
            if (parentCategory == null) {
                throw new RuntimeException("父分类不存在：ID=" + request.getParentId());
            }
            // 三级限制：父分类最多是二级分类
            if (parentCategory.getParentId() != null) {
                ExamCategory grandParent = examCategoryMapper.findById(parentCategory.getParentId());
                if (grandParent != null && grandParent.getParentId() != null) {
                    throw new RuntimeException("只支持三级分类，不能在第三级分类下创建子分类");
                }
            }
            // 父分类必须属于同一科目
            if (!parentCategory.getSubjectId().equals(request.getSubjectId())) {
                throw new RuntimeException("父分类必须属于同一科目");
            }
            // 不能将自己的子孙分类设为父分类（防止循环引用）
            java.util.Set<Long> descendantIds = getDescendantIds(id);
            if (descendantIds.contains(request.getParentId())) {
                throw new RuntimeException("不能将子分类设为父分类");
            }
        }

        // 如果当前分类有子分类，检查变更后是否会超过三级限制
        int childCount = examCategoryMapper.countByParentId(id);
        if (childCount > 0 && request.getParentId() != null) {
            // 计算变更后的层级深度
            int newDepth = 1; // 当前分类本身
            Long parentId = request.getParentId();
            while (parentId != null) {
                newDepth++;
                ExamCategory parent = examCategoryMapper.findById(parentId);
                parentId = (parent != null) ? parent.getParentId() : null;
            }
            // 计算子分类的最大深度
            int maxChildDepth = getMaxChildDepth(id);
            if (newDepth + maxChildDepth > 3) {
                throw new RuntimeException("变更后将超过三级分类限制，该分类下有子分类");
            }
        }

        // 记录旧名称，用于同步更新题目标签
        String oldName = existingCategory.getName();
        String newName = request.getName();
        Long subjectId = existingCategory.getSubjectId();

        // 更新分类实体
        ExamCategory category = new ExamCategory();
        category.setId(id);
        BeanUtils.copyProperties(request, category);

        // 更新数据库
        int rows = examCategoryMapper.update(category);
        if (rows == 0) {
            throw new RuntimeException("更新分类失败");
        }

        // 如果分类名称发生变更，同步更新所有引用该分类的题目
        if (!oldName.equals(newName)) {
            syncUpdateQuestionCategories(subjectId, oldName, newName);
        }

        // 返回带科目名称的VO
        ExamCategoryVO vo = convertToVO(category);
        vo.setSubjectName(subject.getName());
        return vo;
    }

    /**
     * 同步更新题目表中的分类名称
     * 当分类名称变更时，批量更新所有引用该分类的题目
     * 
     * @param subjectId 科目ID
     * @param oldName   旧分类名称
     * @param newName   新分类名称
     */
    private void syncUpdateQuestionCategories(Long subjectId, String oldName, String newName) {
        // 更新真题表
        int examUpdated = examCategoryMapper.updateExamQuestionCategoryName(subjectId, oldName, newName);
        // 更新模拟题表
        int mockUpdated = examCategoryMapper.updateMockQuestionCategoryName(subjectId, oldName, newName);

        // 记录日志（可选）
        int totalUpdated = examUpdated + mockUpdated;
        if (totalUpdated > 0) {
            System.out.println(String.format("[分类同步] 分类名称从 '%s' 更新为 '%s'，共更新 %d 道题目（真题:%d, 模拟题:%d）",
                    oldName, newName, totalUpdated, examUpdated, mockUpdated));
        }
    }

    @Override
    @Transactional
    public void deleteCategory(Long id) {
        // 检查分类是否存在
        ExamCategory existingCategory = examCategoryMapper.findById(id);
        if (existingCategory == null) {
            throw new RuntimeException("分类不存在：ID=" + id);
        }

        // 检查是否有子分类（有子分类时级联删除，或先警告）
        int childCount = examCategoryMapper.countByParentId(id);
        if (childCount > 0) {
            throw new RuntimeException("该分类下有 " + childCount + " 个子分类，请先删除子分类");
        }

        // 删除分类
        int rows = examCategoryMapper.deleteById(id);
        if (rows == 0) {
            throw new RuntimeException("删除分类失败");
        }
    }

    @Override
    public int checkCategoryUsage(Long id) {
        ExamCategory category = examCategoryMapper.findById(id);
        if (category == null) {
            return 0;
        }

        // 统计所有题型的引用数量
        int examCount = examCategoryMapper.countExamQuestionsByCategory(
                category.getSubjectId(), category.getName());
        int mockCount = examCategoryMapper.countMockQuestionsByCategory(
                category.getSubjectId(), category.getName());

        return examCount + mockCount;
    }

    @Override
    public java.util.Map<String, Object> getCategoryStats(String questionType) {
        // 默认统计真题
        String type = (questionType == null || questionType.isEmpty()) ? "exam" : questionType;

        java.util.Map<String, Object> result = new java.util.HashMap<>();

        // 获取所有科目
        List<com.web408.pojo.entity.Subject> subjects = subjectMapper.findAllEnabled();

        // 统计各科目的去重题目数
        java.util.List<java.util.Map<String, Object>> subjectStats = new java.util.ArrayList<>();
        for (com.web408.pojo.entity.Subject subject : subjects) {
            java.util.Map<String, Object> stat = new java.util.HashMap<>();
            stat.put("subjectId", subject.getId());
            stat.put("subjectName", subject.getName());
            // 去重后的题目数（有标签的题目）
            stat.put("questionCount", examCategoryMapper.countDistinctQuestionsBySubject(subject.getId(), type));
            subjectStats.add(stat);
        }
        result.put("subjectStats", subjectStats);

        // 统计全局去重题目总数
        result.put("totalQuestionCount", examCategoryMapper.countDistinctQuestionsTotal(type));

        return result;
    }

    /**
     * 将实体转换为VO
     */
    private ExamCategoryVO convertToVO(ExamCategory category) {
        ExamCategoryVO vo = new ExamCategoryVO();
        BeanUtils.copyProperties(category, vo);
        return vo;
    }
}
