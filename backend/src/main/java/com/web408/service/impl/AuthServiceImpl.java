package com.web408.service.impl;

import com.web408.pojo.dto.LoginDTO;
import com.web408.pojo.dto.RegisterDTO;
import com.web408.pojo.entity.User;
import com.web408.pojo.vo.AuthVO;
import com.web408.mapper.UserMapper;
import com.web408.service.AuthService;
import com.web408.util.BCryptUtil;
import com.web408.util.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * 认证服务实现类
 * 遵循KISS原则：业务逻辑清晰简单
 * 遵循单一职责原则：只处理认证相关业务
 */
@Service
public class AuthServiceImpl implements AuthService {

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private BCryptUtil bCryptUtil;

    @Autowired
    private JwtUtil jwtUtil;

    /**
     * 用户注册
     * 1. 检查用户名是否已存在
     * 2. BCrypt加密密码
     * 3. 插入用户记录
     * 
     * @param request 注册请求
     * @return true-注册成功，false-注册失败
     */
    @Override
    public boolean register(RegisterDTO request) {
        // 检查用户名是否已存在
        User existUser = userMapper.findByUsername(request.getUsername());
        if (existUser != null) {
            throw new RuntimeException("用户名已存在");
        }

        // 创建用户对象
        User user = new User();
        user.setUsername(request.getUsername());
        // BCrypt加密密码
        user.setPassword(bCryptUtil.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        // 默认角色为GUEST
        user.setRole("GUEST");
        user.setEnabled(true);

        // 插入数据库
        int rows = userMapper.insert(user);
        return rows > 0;
    }

    /**
     * 用户登录
     * 1. 查询用户是否存在
     * 2. 验证密码
     * 3. 检查账户是否启用
     * 4. 生成JWT Token
     * 
     * @param request 登录请求
     * @return AuthResponse对象（包含Token）
     */
    @Override
    public AuthVO login(LoginDTO request) {
        // 查询用户
        User user = userMapper.findByUsername(request.getUsername());
        if (user == null) {
            throw new RuntimeException("用户名或密码错误");
        }

        // 验证密码
        if (!bCryptUtil.matches(request.getPassword(), user.getPassword())) {
            throw new RuntimeException("用户名或密码错误");
        }

        // 检查账户是否启用
        if (!user.getEnabled()) {
            throw new RuntimeException("账户已被禁用");
        }

        // 生成JWT Token
        String token = jwtUtil.generateToken(user.getUsername(), user.getRole());

        // 返回认证响应（Token永不过期）
        return new AuthVO(
                token,
                user.getUsername(),
                user.getRole());
    }
}
