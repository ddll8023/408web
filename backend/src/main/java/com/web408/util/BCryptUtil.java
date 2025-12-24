package com.web408.util;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Component;

/**
 * BCrypt密码加密工具类
 * 用于密码的加密和验证
 * 
 * Source: Spring Security BCryptPasswordEncoder
 */
@Component
public class BCryptUtil {

    /**
     * BCrypt密码编码器（强度因子10）
     */
    private static final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(10);

    /**
     * 加密密码
     * 
     * @param rawPassword 明文密码
     * @return BCrypt加密后的密码
     */
    public String encode(String rawPassword) {
        return encoder.encode(rawPassword);
    }

    /**
     * 验证密码
     * 
     * @param rawPassword 明文密码
     * @param encodedPassword BCrypt加密后的密码
     * @return true-密码匹配，false-密码不匹配
     */
    public boolean matches(String rawPassword, String encodedPassword) {
        return encoder.matches(rawPassword, encodedPassword);
    }

    /**
     * 获取BCryptPasswordEncoder实例
     * 
     * @return BCryptPasswordEncoder对象
     */
    public BCryptPasswordEncoder getEncoder() {
        return encoder;
    }
}

