package com.web408.service.impl;

import com.web408.mapper.SubjectMapper;
import com.web408.pojo.dto.SubjectDTO;
import com.web408.pojo.entity.Subject;
import com.web408.pojo.vo.SubjectVO;
import com.web408.service.SubjectService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 科目服务实现类
 * 用途：实现科目管理的业务逻辑
 * 遵循KISS原则：简单直接的业务实现
 */
@Service
public class SubjectServiceImpl implements SubjectService {

    @Autowired
    private SubjectMapper subjectMapper;

    @Override
    public List<SubjectVO> getAllSubjects() {
        List<Subject> subjects = subjectMapper.findAll();
        return subjects.stream()
                .map(this::convertToVO)
                .collect(Collectors.toList());
    }

    @Override
    public List<SubjectVO> getEnabledSubjects() {
        // 直接返回带题目统计的科目列表
        return subjectMapper.findAllEnabledWithStats();
    }

    @Override
    public SubjectVO getSubjectById(Long id) {
        Subject subject = subjectMapper.findById(id);
        if (subject == null) {
            throw new RuntimeException("科目不存在：ID=" + id);
        }
        return convertToVO(subject);
    }

    @Override
    public SubjectVO getSubjectByCode(String code) {
        Subject subject = subjectMapper.findByCode(code);
        if (subject == null) {
            throw new RuntimeException("科目不存在：编码=" + code);
        }
        return convertToVO(subject);
    }

    @Override
    @Transactional
    public SubjectVO createSubject(SubjectDTO request) {
        // 检查名称是否已存在
        if (subjectMapper.existsByName(request.getName(), null) > 0) {
            throw new RuntimeException("科目名称已存在：" + request.getName());
        }

        // 检查编码是否已存在
        if (subjectMapper.existsByCode(request.getCode(), null) > 0) {
            throw new RuntimeException("科目编码已存在：" + request.getCode());
        }

        // 创建科目实体
        Subject subject = new Subject();
        BeanUtils.copyProperties(request, subject);

        // 插入数据库
        int rows = subjectMapper.insert(subject);
        if (rows == 0) {
            throw new RuntimeException("创建科目失败");
        }

        return convertToVO(subject);
    }

    @Override
    @Transactional
    public SubjectVO updateSubject(Long id, SubjectDTO request) {
        // 检查科目是否存在
        Subject existingSubject = subjectMapper.findById(id);
        if (existingSubject == null) {
            throw new RuntimeException("科目不存在：ID=" + id);
        }

        // 检查名称是否已被其他科目使用
        if (subjectMapper.existsByName(request.getName(), id) > 0) {
            throw new RuntimeException("科目名称已被其他科目使用：" + request.getName());
        }

        // 检查编码是否已被其他科目使用
        if (subjectMapper.existsByCode(request.getCode(), id) > 0) {
            throw new RuntimeException("科目编码已被其他科目使用：" + request.getCode());
        }

        // 更新科目实体
        Subject subject = new Subject();
        subject.setId(id);
        BeanUtils.copyProperties(request, subject);

        // 更新数据库
        int rows = subjectMapper.update(subject);
        if (rows == 0) {
            throw new RuntimeException("更新科目失败");
        }

        return convertToVO(subject);
    }

    @Override
    @Transactional
    public void deleteSubject(Long id) {
        // 检查科目是否存在
        Subject existingSubject = subjectMapper.findById(id);
        if (existingSubject == null) {
            throw new RuntimeException("科目不存在：ID=" + id);
        }

        // 删除科目（外键级联会自动删除关联的章节）
        int rows = subjectMapper.deleteById(id);
        if (rows == 0) {
            throw new RuntimeException("删除科目失败");
        }
    }

    /**
     * 将实体转换为VO
     * 遵循YAGNI原则：只转换必要的字段
     */
    private SubjectVO convertToVO(Subject subject) {
        SubjectVO vo = new SubjectVO();
        BeanUtils.copyProperties(subject, vo);
        return vo;
    }
}

