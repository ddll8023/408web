package com.web408.mapper;

import com.web408.pojo.entity.Chapter;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 章节Mapper接口
 * 用途：章节数据的持久层操作
 * 遵循KISS原则：提供基础CRUD操作
 */
@Mapper
public interface ChapterMapper {
    /**
     * 根据科目ID查询所有章节（按排序序号升序）
     * @param subjectId 科目ID
     * @return 章节列表
     */
    List<Chapter> findBySubjectId(@Param("subjectId") Long subjectId);

    /**
     * 根据科目ID查询所有启用的章节（按排序序号升序）
     * @param subjectId 科目ID
     * @return 启用的章节列表
     */
    List<Chapter> findEnabledBySubjectId(@Param("subjectId") Long subjectId);

    /**
     * 根据ID查询章节
     * @param id 章节ID
     * @return 章节实体
     */
    Chapter findById(@Param("id") Long id);

    /**
     * 根据父章节ID查询子章节（按排序序号升序）
     * @param parentId 父章节ID（NULL表示查询顶级章节）
     * @param subjectId 科目ID
     * @return 子章节列表
     */
    List<Chapter> findByParentId(@Param("parentId") Long parentId, @Param("subjectId") Long subjectId);

    /**
     * 创建章节
     * @param chapter 章节实体
     * @return 影响行数
     */
    int insert(Chapter chapter);

    /**
     * 更新章节
     * @param chapter 章节实体
     * @return 影响行数
     */
    int update(Chapter chapter);

    /**
     * 删除章节
     * @param id 章节ID
     * @return 影响行数
     */
    int deleteById(@Param("id") Long id);

    /**
     * 根据科目ID删除所有章节
     * @param subjectId 科目ID
     * @return 影响行数
     */
    int deleteBySubjectId(@Param("subjectId") Long subjectId);

    /**
     * 检查章节名称在同一科目下是否存在
     * @param name 章节名称
     * @param subjectId 科目ID
     * @param parentId 父章节ID
     * @param excludeId 排除的章节ID（用于更新时检查）
     * @return 存在数量
     */
    int existsByName(@Param("name") String name, @Param("subjectId") Long subjectId, 
                     @Param("parentId") Long parentId, @Param("excludeId") Long excludeId);
}

