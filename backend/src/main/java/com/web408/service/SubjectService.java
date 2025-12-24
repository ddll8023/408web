package com.web408.service;

import com.web408.pojo.dto.SubjectDTO;
import com.web408.pojo.vo.SubjectVO;

import java.util.List;

/**
 * 科目服务接口
 * 用途：科目管理的业务逻辑
 * 遵循SOLID原则：接口与实现分离
 */
public interface SubjectService {
    /**
     * 查询所有科目（包含禁用的）
     * @return 科目VO列表
     */
    List<SubjectVO> getAllSubjects();

    /**
     * 查询所有启用的科目
     * @return 科目VO列表
     */
    List<SubjectVO> getEnabledSubjects();

    /**
     * 根据ID查询科目
     * @param id 科目ID
     * @return 科目VO
     */
    SubjectVO getSubjectById(Long id);

    /**
     * 根据编码查询科目
     * @param code 科目编码
     * @return 科目VO
     */
    SubjectVO getSubjectByCode(String code);

    /**
     * 创建科目
     * @param request 科目请求DTO
     * @return 创建的科目VO
     */
    SubjectVO createSubject(SubjectDTO request);

    /**
     * 更新科目
     * @param id 科目ID
     * @param request 科目请求DTO
     * @return 更新后的科目VO
     */
    SubjectVO updateSubject(Long id, SubjectDTO request);

    /**
     * 删除科目
     * @param id 科目ID
     */
    void deleteSubject(Long id);
}

