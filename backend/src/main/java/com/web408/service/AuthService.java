package com.web408.service;

import com.web408.pojo.dto.LoginDTO;
import com.web408.pojo.dto.RegisterDTO;
import com.web408.pojo.vo.AuthVO;

/**
 * 认证服务接口
 * 遵循SOLID原则：依赖倒置，面向接口编程
 */
public interface AuthService {

    /**
     * 用户注册
     * 
     * @param request 注册请求
     * @return true-注册成功，false-注册失败
     */
    boolean register(RegisterDTO request);

    /**
     * 用户登录
     * 
     * @param request 登录请求
     * @return AuthResponse对象（包含Token）
     */
    AuthVO login(LoginDTO request);
}

