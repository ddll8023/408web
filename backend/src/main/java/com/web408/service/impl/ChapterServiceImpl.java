package com.web408.service.impl;

import com.web408.mapper.ChapterMapper;
import com.web408.pojo.dto.ChapterDTO;
import com.web408.pojo.entity.Chapter;
import com.web408.pojo.vo.ChapterVO;
import com.web408.service.ChapterService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 章节服务实现类
 * 用途：实现章节管理的业务逻辑
 * 遵循KISS原则：简单直接的业务实现
 */
@Service
public class ChapterServiceImpl implements ChapterService {

    @Autowired
    private ChapterMapper chapterMapper;

    @Override
    public List<ChapterVO> getChapterTree(Long subjectId) {
        List<Chapter> chapters = chapterMapper.findBySubjectId(subjectId);
        return buildTree(chapters);
    }

    @Override
    public List<ChapterVO> getEnabledChapterTree(Long subjectId) {
        List<Chapter> chapters = chapterMapper.findEnabledBySubjectId(subjectId);
        return buildTree(chapters);
    }

    @Override
    public ChapterVO getChapterById(Long id) {
        Chapter chapter = chapterMapper.findById(id);
        if (chapter == null) {
            throw new RuntimeException("章节不存在：ID=" + id);
        }
        return convertToVO(chapter);
    }

    @Override
    @Transactional
    public ChapterVO createChapter(ChapterDTO request) {
        // 检查章节名称在同一父章节下是否已存在
        if (chapterMapper.existsByName(request.getName(), request.getSubjectId(), 
                request.getParentId(), null) > 0) {
            throw new RuntimeException("章节名称已存在：" + request.getName());
        }

        // 如果有父章节，检查父章节是否存在
        if (request.getParentId() != null) {
            Chapter parentChapter = chapterMapper.findById(request.getParentId());
            if (parentChapter == null) {
                throw new RuntimeException("父章节不存在：ID=" + request.getParentId());
            }
            // 检查父章节的科目ID是否一致
            if (!parentChapter.getSubjectId().equals(request.getSubjectId())) {
                throw new RuntimeException("父章节所属科目与当前科目不一致");
            }
        }

        // 创建章节实体
        Chapter chapter = new Chapter();
        BeanUtils.copyProperties(request, chapter);

        // 插入数据库
        int rows = chapterMapper.insert(chapter);
        if (rows == 0) {
            throw new RuntimeException("创建章节失败");
        }

        return convertToVO(chapter);
    }

    @Override
    @Transactional
    public ChapterVO updateChapter(Long id, ChapterDTO request) {
        // 检查章节是否存在
        Chapter existingChapter = chapterMapper.findById(id);
        if (existingChapter == null) {
            throw new RuntimeException("章节不存在：ID=" + id);
        }

        // 检查章节名称是否已被其他章节使用
        if (chapterMapper.existsByName(request.getName(), request.getSubjectId(), 
                request.getParentId(), id) > 0) {
            throw new RuntimeException("章节名称已被其他章节使用：" + request.getName());
        }

        // 如果有父章节，检查父章节是否存在且不能是自己
        if (request.getParentId() != null) {
            if (request.getParentId().equals(id)) {
                throw new RuntimeException("父章节不能是自己");
            }
            Chapter parentChapter = chapterMapper.findById(request.getParentId());
            if (parentChapter == null) {
                throw new RuntimeException("父章节不存在：ID=" + request.getParentId());
            }
            // 检查父章节的科目ID是否一致
            if (!parentChapter.getSubjectId().equals(request.getSubjectId())) {
                throw new RuntimeException("父章节所属科目与当前科目不一致");
            }
        }

        // 更新章节实体
        Chapter chapter = new Chapter();
        chapter.setId(id);
        BeanUtils.copyProperties(request, chapter);

        // 更新数据库
        int rows = chapterMapper.update(chapter);
        if (rows == 0) {
            throw new RuntimeException("更新章节失败");
        }

        return convertToVO(chapter);
    }

    @Override
    @Transactional
    public void deleteChapter(Long id) {
        // 检查章节是否存在
        Chapter existingChapter = chapterMapper.findById(id);
        if (existingChapter == null) {
            throw new RuntimeException("章节不存在：ID=" + id);
        }

        // 删除章节（外键级联会自动删除子章节）
        int rows = chapterMapper.deleteById(id);
        if (rows == 0) {
            throw new RuntimeException("删除章节失败");
        }
    }

    /**
     * 构建章节树形结构
     * 遵循KISS原则：简单的两级树形结构
     */
    private List<ChapterVO> buildTree(List<Chapter> chapters) {
        // 转换为VO列表
        List<ChapterVO> vos = chapters.stream()
                .map(this::convertToVO)
                .collect(Collectors.toList());

        // 按父ID分组
        Map<Long, List<ChapterVO>> childrenMap = vos.stream()
                .filter(vo -> vo.getParentId() != null)
                .collect(Collectors.groupingBy(ChapterVO::getParentId));

        // 构建树形结构
        List<ChapterVO> tree = new ArrayList<>();
        for (ChapterVO vo : vos) {
            if (vo.getParentId() == null) {
                // 顶级章节
                vo.setChildren(childrenMap.getOrDefault(vo.getId(), new ArrayList<>()));
                tree.add(vo);
            }
        }

        return tree;
    }

    /**
     * 将实体转换为VO
     * 遵循YAGNI原则：只转换必要的字段
     */
    private ChapterVO convertToVO(Chapter chapter) {
        ChapterVO vo = new ChapterVO();
        BeanUtils.copyProperties(chapter, vo);
        vo.setChildren(new ArrayList<>()); // 初始化子章节列表
        return vo;
    }
}

