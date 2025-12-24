package com.web408.filter;

import com.web408.util.JwtUtil;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;

/**
 * JWT认证过滤器
 * 从请求头中提取JWT Token，验证后设置到Spring Security上下文
 * 遵循KISS原则：简单的Token验证逻辑
 * 
 * Source: Spring Security 6 官方文档
 */
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private JwtUtil jwtUtil;

    /**
     * 过滤器核心逻辑
     * 1. 从请求头提取Token
     * 2. 验证Token有效性
     * 3. 解析用户信息并设置到Security上下文
     */
    @Override
    protected void doFilterInternal(HttpServletRequest request, 
                                    HttpServletResponse response, 
                                    FilterChain filterChain) throws ServletException, IOException {
        // 获取Authorization请求头
        String authHeader = request.getHeader("Authorization");

        // 检查Token是否存在且格式正确
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            // 提取Token（去掉"Bearer "前缀）
            String token = authHeader.substring(7);

            // 验证Token
            if (jwtUtil.validateToken(token)) {
                // 从Token中提取用户信息
                String username = jwtUtil.getUsernameFromToken(token);
                String role = jwtUtil.getRoleFromToken(token);

                // 创建Authentication对象
                // 角色需要添加"ROLE_"前缀（Spring Security要求）
                SimpleGrantedAuthority authority = new SimpleGrantedAuthority("ROLE_" + role);
                UsernamePasswordAuthenticationToken authentication = 
                    new UsernamePasswordAuthenticationToken(
                        username, 
                        null, 
                        Collections.singletonList(authority)
                    );

                // 设置到Security上下文
                SecurityContextHolder.getContext().setAuthentication(authentication);
            }
        }

        // 继续过滤器链
        filterChain.doFilter(request, response);
    }
}

