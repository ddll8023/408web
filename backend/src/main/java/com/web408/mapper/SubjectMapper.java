package com.web408.mapper;

import com.web408.pojo.entity.Subject;
import com.web408.pojo.vo.SubjectVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 科目Mapper接口
 * 用途：科目数据的持久层操作
 * 遵循KISS原则：提供基础CRUD操作
 */
@Mapper
public interface SubjectMapper {
    /**
     * 查询所有科目（按排序序号升序）
     * @return 科目列表
     */
    List<Subject> findAll();

    /**
     * 查询所有启用的科目（按排序序号升序）
     * @return 启用的科目列表
     */
    List<Subject> findAllEnabled();

    /**
     * 根据ID查询科目
     * @param id 科目ID
     * @return 科目实体
     */
    Subject findById(@Param("id") Long id);

    /**
     * 根据编码查询科目
     * @param code 科目编码
     * @return 科目实体
     */
    Subject findByCode(@Param("code") String code);

    /**
     * 创建科目
     * @param subject 科目实体
     * @return 影响行数
     */
    int insert(Subject subject);

    /**
     * 更新科目
     * @param subject 科目实体
     * @return 影响行数
     */
    int update(Subject subject);

    /**
     * 删除科目
     * @param id 科目ID
     * @return 影响行数
     */
    int deleteById(@Param("id") Long id);

    /**
     * 检查科目名称是否存在
     * @param name 科目名称
     * @param excludeId 排除的科目ID（用于更新时检查）
     * @return 存在数量
     */
    int existsByName(@Param("name") String name, @Param("excludeId") Long excludeId);

    /**
     * 检查科目编码是否存在
     * @param code 科目编码
     * @param excludeId 排除的科目ID（用于更新时检查）
     * @return 存在数量
     */
    int existsByCode(@Param("code") String code, @Param("excludeId") Long excludeId);

    /**
     * 查询所有启用的科目（带题目统计）
     * @return 科目VO列表（包含questionCount）
     */
    List<SubjectVO> findAllEnabledWithStats();
}

